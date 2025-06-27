import logging
import schedule
import time

from secretary import logger
from secretary.config import load_all_configs
from secretary.database import UserTable
from secretary.todo_emailer import get_todos_to_remind_today
from secretary.todo_emailer import send_email


def email_daily_todos() -> None:
    logging.info('Email daily todos')
    calender_tuples = {
        (row['todo_calendar_id'], row['user_id'])
        for row in
        UserTable.table.scan(ProjectionExpression='todo_calendar_id, user_id')['Items']
    }
    for (calendar_id, user_id) in calender_tuples:
        for event in get_todos_to_remind_today(calendar_id, user_id):
            logging.info(f'Sent mail to {user_id}')
            send_email(user_id, event)


def create_schedule():
    schedule.every().day.at('07:00').do(email_daily_todos)


def start():
    logger.init('secretary_job_scheduler')
    load_all_configs()

    create_schedule()

    logging.info('Created schedule:')
    for job in schedule.jobs:
        logging.info(job)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    start()
