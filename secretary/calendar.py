from typing import Optional

import arrow
from apiclient import discovery
from functools import lru_cache
from pytz import timezone  # type: ignore

from secretary.google_apis import get_google_apis_creds


TZ = timezone('US/Pacific')


@lru_cache(maxsize=1)
def get_calendar_service(user_id: str):
    return discovery.build('calendar', 'v3', credentials=get_google_apis_creds(user_id))


def event_start_time(event: dict) -> arrow.Arrow:
    event_start = event['start']
    return arrow.get(event_start.get('dateTime') or event_start.get('date'))


def event_reminder_time(event: dict) -> Optional[arrow.Arrow]:
    for reminder in event['reminders']['overrides']:
        if reminder['method'] == 'popup':
            return event_start_time(event).shift(minutes=-reminder['minutes'])
    return None
