from __future__ import annotations

from typing import Any

import arrow
import googlemaps
import textwrap
from agents import Agent as OpenAIAgent
from agents import FunctionTool
from agents import function_tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from googleapiclient.discovery import Resource
from pydantic import BaseModel


class Todo(BaseModel):
    summary: str
    due_date: str
    description: str | None = None
    location: str | None = None
    resolved_date: str | None = None

    def to_gcal_event(self) -> dict[str, Any]:
        event: dict[str, Any] = {
            'summary': self.summary,
            'start': {'date': self.due_date},
            'end': {'date': self.due_date},
            'extendedProperties': {
                'shared': {
                    'sb_type': 'todo',
                    'sb_resolved_date': self.resolved_date if self.resolved_date else 'null',
                }
            },
        }

        if self.description:
            event['description'] = self.description
        if self.location:
            event['location'] = self.location

        return event

    @classmethod
    def from_gcal_event(cls, event: dict[str, Any]) -> Todo:
        resolved_date = event.get('extendedProperties', {}).get('shared', {}).get('sb_resolved_date')

        return cls(
            summary=event['summary'],
            due_date=event['start']['date'],
            description=event.get('description'),
            location=event.get('location'),
            resolved_date=resolved_date,
        )


class TodoToResolve(BaseModel):
    id: str
    summary: str
    location: str | None = None


class TodosResult(BaseModel):
    todos: list[Todo]
    error_message: str | None = None


class TodoAgent(OpenAIAgent):
    def __init__(
        self,
        calsvc: Resource,
        gmaps_api_key: str,
        model: str = 'gpt-4.1-mini',
    ) -> None:
        user_tz = calsvc.settings().get(setting='timezone').execute().get('value')

        super().__init__(
            name=self.__class__.__name__,
            model=model,
            instructions=RECOMMENDED_PROMPT_PREFIX + '\n\n' + textwrap.dedent(
                '''\
                # Instructions

                Use the provided tools to search, create, and resolve todos.

                ## Guidelines

                - When searching for upcoming todos, default to next 6 months
                - When searching for past todos, default to last 6 months
                - when searching for todos in an unspecified time range, default to -6 months to +6 months
                - When listing todos to mark as resolved, default to -1 month to +1 month
                - When resolving a todo, make the resolved date today if not specified

                # Current Time & Time Zone

                {current_time}
                '''
            ).format(
                current_time=arrow.now(user_tz).format('YYYY-MM-DDTHH:mm:ssZZ'),
            ),
            output_type=str,
            tools=[
                search_todos_wrapper(calsvc, user_tz),  # type: ignore
                create_todo_wrapper(calsvc, gmaps_api_key, user_tz),  # type: ignore
                lookup_todo_id_for_resolving_wrapper(calsvc, user_tz),  # type: ignore
                resolve_todo_wrapper(calsvc, user_tz),  # type: ignore
            ],
        )


def search_todos_wrapper(cal: Resource, user_tz: str) -> FunctionTool:
    @function_tool
    async def search_todos(
        due_date_min: str,
        due_date_max: str,
    ) -> TodosResult:
        """
        due_date_min, due_date_max: format should be YYYY-MM-DD
        """

        time_min = arrow.get(due_date_min).floor('day').replace(tzinfo=user_tz).isoformat()
        time_max = arrow.get(due_date_max).ceil('day').replace(tzinfo=user_tz).isoformat()

        events_result = cal.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=1001,
            singleEvents=True,
            orderBy='startTime',
            sharedExtendedProperty='sb_type=todo',
        ).execute()

        todos = [
            Todo.from_gcal_event(event)
            for event in events_result.get('items', [])
        ]

        if len(todos) > 1000:
            return TodosResult(todos=[], error_message='Too many todos found. Narrow the time range and try again.')

        return TodosResult(todos=todos, error_message=None)

    return search_todos


def create_todo_wrapper(cal: Resource, gmaps_api_key: str, user_tz: str) -> FunctionTool:
    @function_tool
    async def create_todo(
        summary: str,
        due_date: str,
        description: str | None,
        location: str | None,
    ) -> str:
        """
        due_date: format should be YYYY-MM-DD
        location: look up and append address to location
        """

        if location:
            gmaps = googlemaps.Client(key=gmaps_api_key)
            places = gmaps.places(query=location)['results']
            if len(places) == 1:
                location += ' ' + places[0]['formatted_address']

        todo = Todo(
            summary='📝 ' + summary,
            due_date=due_date,
            description=description,
            location=location,
        )

        cal.events().insert(
            calendarId='primary',
            body=todo.to_gcal_event(),
        ).execute()

        return 'Successfully created todo'

    return create_todo


def lookup_todo_id_for_resolving_wrapper(cal: Resource, user_tz: str) -> FunctionTool:
    @function_tool
    async def lookup_todo_id_for_resolving(
        due_date_min: str,
        due_date_max: str,
    ) -> list[TodoToResolve]:
        """
        summary: the summary of the todo to resolve
        due_date_min, due_date_max: format should be YYYY-MM-DD
        """

        time_min = arrow.get(due_date_min).floor('day').replace(tzinfo=user_tz).isoformat()
        time_max = arrow.get(due_date_max).ceil('day').replace(tzinfo=user_tz).isoformat()

        events_result = cal.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=1001,
            singleEvents=True,
            orderBy='startTime',
            sharedExtendedProperty=['sb_type=todo', 'sb_resolved_date=null'],
        ).execute()

        todos_to_resolve = [
            TodoToResolve(
                id=event['id'],
                summary=event['summary'],
                location=event.get('location'),
            )
            for event in events_result.get('items', [])
            if event.get('extendedProperties', {}).get('shared', {}).get('sb_type') == 'todo'
        ]

        return todos_to_resolve

    return lookup_todo_id_for_resolving


def resolve_todo_wrapper(cal: Resource, user_tz: str) -> FunctionTool:
    @function_tool
    async def resolve_todo(
        todo_id: str,
        resolved_date: str,
    ) -> str:
        """
        resolved_date: format should be YYYY-MM-DD
        """
        event = cal.events().get(calendarId='primary', eventId=todo_id).execute()

        now = arrow.now(user_tz).format('YYYY-MM-DD')
        if not resolved_date:
            resolved_date = now

        assert resolved_date <= now

        if not event.get('extendedProperties', {}).get('shared', {}).get('sb_type') == 'todo':
            return 'This event is not a todo.'

        event['summary'] = event['summary'].replace('📝 ', '✅ ')
        event['extendedProperties']['shared']['sb_resolved_date'] = resolved_date

        cal.events().update(
            calendarId='primary',
            eventId=todo_id,
            body=event,
        ).execute()

        return 'Successfully resolved todo'

    return resolve_todo
