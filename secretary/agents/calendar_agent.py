from __future__ import annotations

from typing import cast

import arrow
import googlemaps
import textwrap
import yaml
from agents import Agent as OpenAIAgent
from agents import function_tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from pydantic import BaseModel

from secretary.agents.base import UserContext
from secretary.agents.base import UserContextWrapper
from secretary.google_apis import get_calendar_service
from secretary.data_models.event import Event
from secretary.service_config import cfg


class CalendarAgent(OpenAIAgent):
    def __init__(
        self,
        user_ctx: UserContext,
        model: str = 'gpt-4.1-mini',
    ) -> None:
        calsvc = get_calendar_service(user_ctx.user_id)
        user_tz = calsvc.settings().get(setting='timezone').execute().get('value')

        calendar_names_and_ids = yaml.dump(
            [
                '[id: {id}] {name}{primary}'.format(
                    id=cal['id'],
                    name=cal.get('summaryOverride') or cal['summary'],
                    primary=' (primary)' if cal.get('primary', False) else '',
                )
                for cal in calsvc.calendarList().list().execute().get('items', [])
            ]
        )

        super().__init__(
            name=self.__class__.__name__,
            model=model,
            instructions=RECOMMENDED_PROMPT_PREFIX + '\n\n' + textwrap.dedent(
                '''\
                # Instructions

                Use the provided tools to interact with the user's Google Calendars.

                ## Searching For Events

                1. Identify which calendars are relevant to the request based on calendar names
                2. Identify which calendars are irrelevant
                3. Search only within the relevant calendars

                ### Example

                Suppose I have the following calendars:

                - primary
                - work
                - family
                - construction project

                - "What events do I have tomorrow?" -> search all calendars for events on the next day
                - "When is my next work meeting?" -> search work and primary calendars
                - "Where is my consult with the architect?" -> search construction project and primary calendars

                ## Creating Events

                - by default, create all events in the primary calendar only
                - only create events in other calendars if the user explicitly specifies it

                # Current Time & Time Zone

                {current_time}

                ## Available Calendars

                {calendar_names_and_ids}
                '''
            ).format(
                current_time=arrow.now(user_tz).isoformat(),
                calendar_names_and_ids=calendar_names_and_ids,
            ),
            output_type=str,
            tools=[
                list_events,
                create_event,
            ],
        )

    @classmethod
    def simplify_event_dict(cls, orig: dict) -> dict:
        simplified = {}

        if 'summary' in orig:
            simplified['summary'] = orig['summary']
        if 'location' in orig:
            simplified['location'] = orig['location']
        if 'start' in orig:
            simplified['start'] = orig['start']
        if 'end' in orig:
            simplified['end'] = orig['end']
        if 'recurringEventId' in orig:
            simplified['is_recurring'] = True

        return simplified


class EventsResult(BaseModel):
    events: list[Event]
    error_message: str | None = None


@function_tool
async def list_events(
    ctx: UserContextWrapper,
    calendar_id: str,
    time_min: str,
    time_max: str,
) -> EventsResult:
    """
    time_min, time_max: format should be RFC3339 (YYYY-MM-DDTHH:mm:ssZZ)
    """
    calsvc = get_calendar_service(cast(UserContext, ctx.context).user_id)

    max_results = 1001

    event_dicts = calsvc.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime',
    ).execute().get('items', [])

    if len(event_dicts) >= max_results:
        return EventsResult(events=[], error_message='Too many events found. Narrow the time range and try again.')

    events = [
        Event.from_gcal_event(d)
        for d in event_dicts
        if d.get('extendedProperties', {}).get('shared', {}).get('sb_type') != 'todo'
    ]

    return EventsResult(events=events, error_message=None)


@function_tool
async def create_event(
    ctx: UserContextWrapper,
    calendar_id: str,
    summary: str,
    start: str,
    end: str,
    location: str | None,
    is_all_day_event: bool,
) -> str:
    """
    start, end: format should be RFC3339 (YYYY-MM-DDTHH:mm:ssZZ)
    location: look up and append address to location

    - if start and end are both not provided, assume all day event
    - if start is provided and end is not, assume 1 hour duration
    """
    calsvc = get_calendar_service(cast(UserContext, ctx.context).user_id)

    if location:
        gmaps = googlemaps.Client(key=cfg().google_apis.api_key)
        places = gmaps.places(query=location)['results']
        if len(places) == 1:
            location += ' ' + places[0]['formatted_address']

    if is_all_day_event:
        start = arrow.get(start).format('YYYY-MM-DD')
        end = arrow.get(end).format('YYYY-MM-DD')
    else:
        start = arrow.get(start).isoformat()
        end = arrow.get(end).isoformat()

    event = Event(
        summary=summary,
        start=start,
        end=end,
        location=location,
    )

    calsvc.events().insert(
        calendarId=calendar_id,
        body=event.to_gcal_event(),
    ).execute()

    return 'Successfully created event'
