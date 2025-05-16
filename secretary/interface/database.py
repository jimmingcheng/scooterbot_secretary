import boto3
from typing import Any


class NoSuchUserError(Exception):
    pass


def get_user_table() -> Any:
    return boto3.resource('dynamodb', 'us-west-2').Table('scooterbot_secretary_user')


def get_channel_table() -> Any:
    return boto3.resource('dynamodb', 'us-west-2').Table('scooterbot_secretary_channel')


def get_oauth_table() -> Any:
    return boto3.resource('dynamodb', 'us-west-2').Table('scooterbot_secretary_oauth')


class UserTable:
    table = get_user_table()

    def upsert(self, user_id: str, todo_calendar_id: str) -> None:
        self.table.put_item(Item={
            'user_id': user_id,
            'todo_calendar_id': todo_calendar_id,
        })

    def get(self, user_id: str) -> dict:
        try:
            return self.table.get_item(Key={'user_id': user_id})['Item']
        except KeyError:
            raise NoSuchUserError(user_id)

    def delete(self, user_id: str) -> None:
        self.table.delete_item(Key={'user_id': user_id})


class ChannelTable:
    table = get_channel_table()

    @classmethod
    def channel_id(cls, channel_type: str, channel_user_id: str) -> str:
        return f'{channel_type}:{channel_user_id}'

    def upsert(self, channel_type: str, channel_user_id: str, user_id: str) -> None:
        self.table.put_item(Item={
            'channel_id': ChannelTable.channel_id(channel_type, channel_user_id),
            'channel_type': channel_type,
            'channel_user_id': channel_user_id,
            'user_id': user_id,
        })

    def get(self, channel_type: str, channel_user_id: str) -> dict:
        try:
            channel_id = ChannelTable.channel_id(channel_type, channel_user_id)
            return self.table.get_item(Key={'channel_id': channel_id})['Item']
        except KeyError:
            raise NoSuchUserError(channel_user_id)

    def look_up_user_id(self, channel_type: str, channel_user_id: str) -> str:
        channel_id = ChannelTable.channel_id(channel_type, channel_user_id)
        return self.table.get_item(Key={'channel_id': channel_id})['Item']['user_id']


def disconnect_channel(user_id: str) -> None:
    pass
