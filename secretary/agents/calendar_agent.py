from __future__ import annotations

from typing import Any

import arrow
import googlemaps
import textwrap
import yaml
from agents import Agent as OpenAIAgent
from agents import FunctionTool
from agents import function_tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from googleapiclient.discovery import Resource


class CalendarAgent(OpenAIAgent):
    def __init__(
        self,
        calsvc: Resource,
        gmaps_api_key: str,
        model: str = 'gpt-4.1-mini',
    ) -> None:
        calendar_time_zone = calsvc.settings().get(setting='timezone').execute().get('value')

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

                Use the provided tools to interact with the Google Calendar API.

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

                # Current Time

                {current_time} ({time_zone})

                ## Available Calendars

                {calendar_names_and_ids}
                '''
            ).format(
                current_time=arrow.now(calendar_time_zone).format('YYYY-MM-DDTHH:mm:ssZZ'),
                time_zone=calendar_time_zone,
                calendar_names_and_ids=calendar_names_and_ids,
            ),
            output_type=str,
            tools=[
                search_events_wrapper(calsvc),  # type: ignore
                create_event_wrapper(calsvc, gmaps_api_key),  # type: ignore
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


def search_events_wrapper(cal: Resource) -> FunctionTool:
    @function_tool
    async def search_events(
        calendar_id: str,
        time_min: str | None,
        time_max: str | None,
    ) -> str:
        """
        time_min, time_max: format should be YYYY-MM-DDTHH:mm:ssZZ
        """
        events_result = cal.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=1001,
            singleEvents=True,
            orderBy='startTime',
        ).execute()

        events = [
            CalendarAgent.simplify_event_dict(event)
            for event in events_result.get('items', [])
        ]

        if len(events) > 1000:
            return 'Too many events. Narrow the time range and try again.'

        return yaml.dump(events)

    return search_events


def create_event_wrapper(cal: Resource, gmaps_api_key: str) -> FunctionTool:
    @function_tool
    async def create_event(
        calendar_id: str,
        summary: str,
        description: str | None,
        location: str | None,
        start: str | None,
        end: str | None,
        is_all_day_event: bool,
    ) -> str:
        """
        start, end: format should be YYYY-MM-DDTHH:mm:ssZZ
        location: look up and append address to location

        - if start and end are both not provided, assume all day event
        - if start is provided and end is not, assume 1 hour duration
        """
        event: dict[str, Any] = {}
        if summary:
            event['summary'] = summary
        if description:
            event['description'] = description
        if location:
            gmaps = googlemaps.Client(key=gmaps_api_key)
            places = gmaps.places(query=location)['results']
            if len(places) == 1:
                event['location'] = location + ' ' + places[0]['formatted_address']
            else:
                event['location'] = location
        if start:
            if is_all_day_event:
                event['start'] = {'date': arrow.get(start).format('YYYY-MM-DD')}
            else:
                event['start'] = {'dateTime': arrow.get(start).format('YYYY-MM-DDTHH:mm:ssZZ')}
        if end:
            if is_all_day_event:
                event['end'] = {'date': arrow.get(end).format('YYYY-MM-DD')}
            else:
                event['end'] = {'dateTime': arrow.get(end).format('YYYY-MM-DDTHH:mm:ssZZ')}

        saved_event = cal.events().insert(
            calendarId=calendar_id,
            body=event,
        ).execute()

        return yaml.dump(CalendarAgent.simplify_event_dict(saved_event))

    return create_event
