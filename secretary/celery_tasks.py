from typing import Any
from typing import Optional

import aiohttp
import arrow
import asyncio
import staticconf
from celery import Celery
from celery.signals import after_setup_logger
from celery.signals import worker_init
from dataclasses import dataclass

import secretary
from secretary.calendar import get_calendar_service
from secretary.database import ChannelTable


REDIS_HOST = 'redis'
app = Celery('celery_tasks', broker='redis://{}'.format(REDIS_HOST))
app.conf.task_default_queue = 'scooterbot_secretary_task_queue'


def google_apis_api_key() -> str:
    return staticconf.read('google_apis.api_key', namespace='secretary')  # type: ignore


@dataclass
class AddCalendarEventArgs:
    title: str
    start_time: str
    end_time: str
    is_all_day: bool
    location: Optional[str]
    confirmation_message: str


@worker_init.connect
def init(**kwargs):
    secretary.init()


@app.task
def add_calendar_event(user_id: str, args_dict: dict) -> None:
    asyncio.run(
        _add_calendar_event(
            user_id,
            AddCalendarEventArgs(
                title=args_dict['title'],
                start_time=args_dict['start_time'],
                end_time=args_dict['end_time'],
                is_all_day=args_dict['is_all_day'],
                location=args_dict.get('location'),
                confirmation_message=args_dict['confirmation_message'],
            )
        )
    )


async def _add_calendar_event(user_id: str, args: AddCalendarEventArgs) -> None:
    start_time = arrow.get(args.start_time)
    end_time = arrow.get(args.end_time)
    event: dict[str, Any] = {
        'summary': args.title
    }

    if args.location:
        async with aiohttp.ClientSession() as session:
            url = f'https://maps.googleapis.com/maps/api/place/textsearch/json?key={google_apis_api_key()}&query={args.location}'

            async with session.get(url) as resp:
                resp_data = await resp.json()
                place = resp_data['results'][0] if resp_data.get('results') else None

                if place:
                    event['location'] = place['formatted_address']

    if args.is_all_day:
        event['start'] = {'date': start_time.format('YYYY-MM-DD')}
        event['end'] = {'date': end_time.format('YYYY-MM-DD')}
    else:
        event['start'] = {'dateTime': start_time.format('YYYY-MM-DDTHH:mm:ssZZ')}
        event['end'] = {'dateTime': end_time.format('YYYY-MM-DDTHH:mm:ssZZ')}

    # aiogoogle doesn't work for some reason
    get_calendar_service(user_id).events().insert(calendarId='primary', body=event).execute()


@after_setup_logger.connect
def setup_logger(logger, *args, **kwargs):
    pass
