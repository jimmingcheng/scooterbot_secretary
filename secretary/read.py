import arrow
from dataclasses import dataclass
from typing import List
from typing import Optional

from secretary.calendar import get_calendar_service
from secretary.database import UserTable
from secretary.calendar import TZ


@dataclass
class Todo:
    task_name: str
    due_date: arrow.Arrow


def get_todos(user_id: str, start_date: arrow.Arrow, end_date: arrow.Arrow) -> List[Todo]:
    user = UserTable.get(user_id)
    todo_calendar_id = user.todo_calendar_id

    resp = get_calendar_service(user_id).events().list(
        calendarId=todo_calendar_id,
        timeMin=start_date.isoformat(),
        timeMax=end_date.isoformat(),
        singleEvents=True,
        orderBy='startTime',
    ).execute()

    todo_events = resp.get('items', [])

    return [
        Todo(
            task_name=event['summary'],
            due_date=arrow.get(event['start']['date']),
        )
        for event in todo_events
    ]


def get_todos_for_day(user_id: str, dt: Optional[arrow.Arrow] = None) -> List[str]:
    if not dt:
        dt = arrow.now(TZ)

    start_of_day = arrow.get(dt.year, dt.month, dt.day, tzinfo=TZ)

    todos = get_todos(user_id, start_of_day, start_of_day.shift(days=1))

    return [todo.task_name for todo in todos]
