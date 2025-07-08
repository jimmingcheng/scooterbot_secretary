from __future__ import annotations

from typing import cast

import arrow
import googlemaps
import textwrap
from agents import Agent as OpenAIAgent
from agents import function_tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from pydantic import BaseModel

from secretary.agents.base import UserContext
from secretary.agents.base import UserContextWrapper
from secretary.calendar import get_calendar_service
from secretary.data_models import Todo
from secretary.service_config import config


class TodosResult(BaseModel):
    todos: list[Todo]
    error_message: str | None = None


class TodoAgent(OpenAIAgent):
    def __init__(
        self,
        user_ctx: UserContext,
        model: str = 'gpt-4.1-mini',
    ) -> None:
        user_tz = get_calendar_service(user_ctx.user_id).settings().get(setting='timezone').execute().get('value')

        super().__init__(
            name=self.__class__.__name__,
            model=model,
            instructions=RECOMMENDED_PROMPT_PREFIX + '\n\n' + textwrap.dedent(
                '''\
                # Instructions

                Use the provided tools to search, create, and resolve/unresolve todos.

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
                current_time=arrow.now(user_tz).isoformat()
            ),
            output_type=str,
            tools=[
                list_todos,
                create_todo,
                update_todo,
                delete_todo,
                resolve_todo,
                unresolve_todo,
            ],
        )


@function_tool
async def list_todos(
    ctx: UserContextWrapper,
    due_date_min: str,
    due_date_max: str,
) -> TodosResult:
    """
    due_date_min, due_date_max: format should be YYYY-MM-DD
    """
    calsvc = get_calendar_service(cast(UserContext, ctx.context).user_id)

    user_tz = calsvc.settings().get(setting='timezone').execute().get('value')
    time_min = arrow.get(due_date_min).floor('day').replace(tzinfo=user_tz).isoformat()
    time_max = arrow.get(due_date_max).ceil('day').replace(tzinfo=user_tz).isoformat()

    max_results = 1001

    event_dicts = calsvc.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime',
        sharedExtendedProperty='sb_type=todo',
    ).execute().get('items', [])

    if len(event_dicts) >= max_results:
        return TodosResult(todos=[], error_message='Too many todos found. Narrow the time range and try again.')

    todos = [
        Todo.from_gcal_event(d)
        for d in event_dicts
    ]

    return TodosResult(todos=todos, error_message=None)


@function_tool
async def create_todo(
    ctx: UserContextWrapper,
    summary: str,
    due_date: str,
    description: str | None,
    location: str | None,
) -> str:
    """
    due_date: format should be YYYY-MM-DD
    location: look up and append address to location
    """
    calsvc = get_calendar_service(cast(UserContext, ctx.context).user_id)

    if location:
        gmaps = googlemaps.Client(key=config.google_apis.api_key)
        places = gmaps.places(query=location)['results']
        if len(places) == 1:
            location += ' ' + places[0]['formatted_address']

    todo = Todo(
        summary='📝 ' + summary,
        due_date=due_date,
        description=description,
        location=location,
    )

    calsvc.events().insert(
        calendarId='primary',
        body=todo.to_gcal_event(),
    ).execute()

    return 'Successfully created todo'


@function_tool
async def resolve_todo(ctx: UserContextWrapper, todo_id: str) -> str:
    calsvc = get_calendar_service(cast(UserContext, ctx.context).user_id)
    todo = Todo.get(calsvc, todo_id)

    if todo.is_resolved:
        return 'This todo is already resolved.'

    todo.resolve()

    calsvc.events().patch(
        calendarId='primary',
        eventId=todo_id,
        body=todo.to_gcal_event(),
    ).execute()

    return 'Marked todo as resolved.'


@function_tool
async def unresolve_todo(ctx: UserContextWrapper, todo_id: str) -> str:
    calsvc = get_calendar_service(cast(UserContext, ctx.context).user_id)
    todo = Todo.get(calsvc, todo_id)

    if not todo.is_resolved:
        return 'This todo was not resolved to begin with.'

    todo.unresolve()

    calsvc.events().patch(
        calendarId='primary',
        eventId=todo_id,
        body=todo.to_gcal_event(),
    ).execute()

    return 'Marked todo as unresolved.'


@function_tool
async def update_todo(
    ctx: UserContextWrapper,
    todo_id: str,
    new_due_date: str | None = None,
    new_summary: str | None = None,
) -> str:
    """
    Only supply attributes that you want to change.

    new_due_date: format should be YYYY-MM-DD
    """
    calsvc = get_calendar_service(cast(UserContext, ctx.context).user_id)
    todo = Todo.get(calsvc, todo_id)

    log_msgs = []

    if new_due_date:
        log_msgs += [f'Due date changed from {todo.due_date} to {new_due_date}']
        todo.due_date = new_due_date

    if new_summary:
        log_msgs += [f'Summary changed from "{todo.summary}" to "{new_summary}"']
        todo.summary = '📝 ' + new_summary

    log_msg = ','.join(log_msgs)

    todo.log_to_description(log_msg)

    calsvc.events().patch(
        calendarId='primary',
        eventId=todo_id,
        body=todo.to_gcal_event(),
    ).execute()

    return log_msg


@function_tool
async def delete_todo(ctx: UserContextWrapper, todo_id: str) -> str:
    calsvc = get_calendar_service(cast(UserContext, ctx.context).user_id)

    calsvc.events().delete(
        calendarId='primary',
        eventId=todo_id,
    ).execute()

    return 'Todo deleted successfully.'
