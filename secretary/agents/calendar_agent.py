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
from secretary.data_models.event import Event
from secretary.google_apis import get_calendar_service
from secretary.service_config import cfg


class CalendarAgent(OpenAIAgent):
    def __init__(
        self,
        user_ctx: UserContext,
        model: str = 'gpt-4.1-mini',
    ) -> None:
        calsvc = get_calendar_service(user_ctx.user_id)
        tz = calsvc.settings().get(setting='timezone').execute().get('value')

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

                ## Listing Events

                1. Identify which calendars are relevant
                2. Identify the relevant time range
                3. List only within the relevant calendars and time range

                ### Identifying Relevant Calendars

                Use the names of the calendars to determine relevance the user's request.

                Assume the primary calendar is relevant by default. Only exclude it if the user
                explicitly states they want to search a different calendar.

                #### Examples

                Suppose I have the following calendar names:

                - Personal (primary)
                - Work
                - Family
                - Construction Project

                - "What events do I have tomorrow?" -> list all calendars for events on the next day
                - "When is my next work meeting?" -> list Work and primary calendars
                - "Where is my consult with the architect?" -> list Construction Project and primary calendars

                ### Identifying Relevant Time Range

                The default time range should be -6 months to +6 months from the current time.

                To manage the number of events scanned, make sure time_max - time_min is at most 1
                year for any particular search. If needed break larger time ranges into multiple
                searches util result is found.

                ## Creating Events

                - by default, create all events in the primary calendar only
                - only create events in other calendars if the user explicitly specifies it

                # Current Time & Time Zone

                {current_time}

                ## Available Calendars

                {calendar_names_and_ids}
                '''
            ).format(
                current_time=arrow.now(tz).isoformat(),
                calendar_names_and_ids=calendar_names_and_ids,
            ),
            output_type=str,
            tools=[
                list_events,
                list_master_instances_for_recurring_events,
                create_event,
                update_event,
                delete_event,
            ],
        )


class EventsResult(BaseModel):
    events: list[Event]
    hide_recurrence_properties: bool = True
    error_message: str | None = None


def events_per_day(
    events: list[dict],
) -> float:
    first_event_start = events[0]['start'].get('dateTime') or events[0]['start']['date']
    last_event_start = events[-1]['start'].get('dateTime') or events[-1]['start']['date']

    days = (
        arrow.get(last_event_start).date() - arrow.get(first_event_start).date()
    ).days

    return len(events) / (days + 1) if days > 0 else len(events)


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
        days = min(
            max_results * 0.8 // events_per_day(event_dicts),
            90,
        )
        new_time_min = arrow.get(time_max).shift(days=-days).isoformat()

        return EventsResult(
            events=[],
            error_message=(
                f'Time range was too wide to query. Try again with time_min={new_time_min} and time_max={time_max}.'
            )
        )

    events = [
        Event.from_gcal_event(d)
        for d in event_dicts
        if d.get('extendedProperties', {}).get('shared', {}).get('sb_type') != 'todo'
    ]

    return EventsResult(events=events, error_message=None)


@function_tool
async def list_master_instances_for_recurring_events(
    ctx: UserContextWrapper,
    calendar_id: str,
) -> EventsResult:
    """
    time_min, time_max: format should be RFC3339 (YYYY-MM-DDTHH:mm:ssZZ)
    """
    calsvc = get_calendar_service(cast(UserContext, ctx.context).user_id)
    tz = calsvc.settings().get(setting='timezone').execute().get('value')

    event_dicts = calsvc.events().list(
        calendarId=calendar_id,
        timeMin=arrow.now(tz).isoformat(),
        timeMax=arrow.now(tz).shift(months=12 + 1).isoformat(),
        maxResults=2500,  # Google API hard max
        singleEvents=False,
    ).execute().get('items', [])

    events = [
        Event.from_gcal_event(d)
        for d in event_dicts
        if (
            d.get('extendedProperties', {}).get('shared', {}).get('sb_type') != 'todo' and d.get('recurrence')
        )
    ]

    return EventsResult(
        events=events,
        hide_recurrence_properties=False,
        error_message=None
    )


@function_tool
async def create_event(
    ctx: UserContextWrapper,
    calendar_id: str,
    summary: str,
    start: str,
    end: str,
    location: str | None,
    is_all_day_event: bool,
    rfc5545_recurrence_properties: list[str] | None,
    notes: str | None,
) -> str:
    """
    start, end: format should be RFC3339 (YYYY-MM-DDTHH:mm:ssZZ)
    location: look up and append address to location

    - if start and end are both not provided, assume all day event
    - if start is provided and end is not, assume 1 hour duration
    """
    calsvc = get_calendar_service(cast(UserContext, ctx.context).user_id)
    tz = calsvc.settings().get(setting='timezone').execute().get('value')

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
        recurrence=rfc5545_recurrence_properties,
    )

    if notes:
        event.log_to_description(notes)

    calsvc.events().insert(
        calendarId=calendar_id,
        body=event.to_gcal_event(calendar_tz=tz),
    ).execute()

    return 'Successfully created event'


@function_tool
async def update_event(
    ctx: UserContextWrapper,
    calendar_id: str,
    event_id: str,
    summary: str | None = None,
    start: str | None = None,
    end: str | None = None,
    location: str | None = None,
    is_all_day_event: bool = False,
    rfc5545_recurrence_properties: list[str] | None = None,
    notes: str | None = None,
) -> str:
    """
    start, end: format should be RFC3339 (YYYY-MM-DDTHH:mm:ssZZ)
    """
    calsvc = get_calendar_service(cast(UserContext, ctx.context).user_id)
    tz = calsvc.settings().get(setting='timezone').execute().get('value')

    event = Event.get(calsvc, calendar_id, event_id)

    if summary:
        event.log_to_description(f'Summary: {event.summary} → {summary}')
        event.summary = summary

    if start:
        event.log_to_description(f'Start: {event.start} → {start}')
        event.start = arrow.get(start).format('YYYY-MM-DD') if is_all_day_event else arrow.get(start).isoformat()

    if end:
        event.log_to_description(f'End: {event.end} → {end}')
        event.end = arrow.get(end).format('YYYY-MM-DD') if is_all_day_event else arrow.get(end).isoformat()

    if location:
        gmaps = googlemaps.Client(key=cfg().google_apis.api_key)
        places = gmaps.places(query=location)['results']
        if len(places) == 1:
            location += ' ' + places[0]['formatted_address']

        event.log_to_description(f'Location: {event.location} → {location}')
        event.location = location

    if rfc5545_recurrence_properties is not None:
        event.log_to_description('Changed recurrence properties')
        event.recurrence = rfc5545_recurrence_properties

    if notes:
        event.log_to_description(notes)

    calsvc.events().patch(
        calendarId=calendar_id,
        eventId=event_id,
        body=event.to_gcal_event(calendar_tz=tz),
    ).execute()

    return 'Successfully updated event'


@function_tool
async def delete_event(
    ctx: UserContextWrapper,
    calendar_id: str,
    event_id: str,
) -> str:
    """
    Deletes an event from the specified calendar.
    """
    calsvc = get_calendar_service(cast(UserContext, ctx.context).user_id)

    calsvc.events().delete(
        calendarId=calendar_id,
        eventId=event_id,
    ).execute()

    return 'Successfully deleted event'
