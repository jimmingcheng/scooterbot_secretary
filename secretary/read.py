import arrow
from typing import List
from typing import Optional

from secretary.calendar import get_calendar_service
from secretary.database import UserTable
from secretary.calendar import TZ


def get_events(user_id: str, time_min: arrow.Arrow, time_max: arrow.Arrow) -> List[dict]:
    user = UserTable().get(user_id)
    google_apis_user_id = user['google_apis_user_id']
    todo_calendar_id = user['todo_calendar_id']

    resp = get_calendar_service(google_apis_user_id).events().list(
        calendarId=todo_calendar_id,
        timeMin=time_min.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,
        orderBy='startTime',
    ).execute()

    return resp.get('items', [])


def get_todos_for_day(user_id: str, dt: Optional[arrow.Arrow] = None) -> List[str]:
    if not dt:
        dt = arrow.now(TZ)

    start_of_day = arrow.get(dt.year, dt.month, dt.day, tzinfo=TZ)

    events = get_events(user_id, start_of_day, start_of_day.shift(days=1))

    return [event['summary'] for event in events]
