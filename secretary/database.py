import boto3
from typing import Any


class NoSuchUserError(Exception):
    pass


def get_user_table() -> Any:
    return boto3.resource('dynamodb', 'us-west-2').Table('scooterbot_secretary_user')


def get_oauth_table() -> Any:
    return boto3.resource('dynamodb', 'us-west-2').Table('scooterbot_secretary_oauth')


class UserTable:
    table = get_user_table()

    def upsert(self, user_id: str, google_apis_user_id: str, todo_calendar_id: str) -> None:
        self.table.put_item(Item={
            'user_id': user_id,
            'google_apis_user_id': google_apis_user_id,
            'todo_calendar_id': todo_calendar_id,
        })

    def get(self, user_id: str) -> dict:
        try:
            return self.table.get_item(Key={'user_id': user_id})['Item']
        except KeyError:
            raise NoSuchUserError(user_id)

    def delete(self, user_id: str) -> None:
        self.table.delete_item(Key={'user_id': user_id})


def remove_account(user_id: str) -> None:
    user = UserTable().get(user_id)
    UserTable().delete(user_id)
    #get_oauth_table().delete_item(Key={'user_id': user['google_apis_user_id']})
