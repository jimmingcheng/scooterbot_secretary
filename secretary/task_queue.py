import logging
from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import RedisAsyncResultBackend
from taskiq_redis import RedisStreamBroker

import secretary


REDIS_HOST = 'redis'

secretary.init()

broker = RedisStreamBroker(
    url=f'redis://{REDIS_HOST}:6379',
    queue_name='secretary',
).with_result_backend(
    RedisAsyncResultBackend(redis_url=f'redis://{REDIS_HOST}:6379')
)

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)


# daily at 7am
@broker.task(schedule=[{'cron': '0 7 * * *'}])
async def email_daily_todos() -> None:
    from secretary.todo_emailer import get_todos_to_remind_today
    from secretary.todo_emailer import send_email
    from secretary.data_models import User

    logging.info('Email daily todos')
    calendar_tuples = {
        (row['todo_calendar_id'], row['user_id'])
        for row in User.table().scan(ProjectionExpression='todo_calendar_id, user_id')['Items']
    }
    for (calendar_id, user_id) in calendar_tuples:
        for event in get_todos_to_remind_today(calendar_id, user_id):
            logging.info(f'Sent mail to {user_id}')
            send_email(user_id, event)
