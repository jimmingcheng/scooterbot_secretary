from typing import Literal

from dataclasses import asdict
from dataclasses import dataclass

import boto3
from boto3.dynamodb.conditions import Key


ChannelType = Literal['alexa', 'discord', 'sms']
LinkableAccountType = Literal['tesla']


class UserDataNotFoundError(Exception):
    pass


@dataclass
class User:
    user_id: str
    todo_calendar_id: str | None


@dataclass
class Channel:
    channel_type: ChannelType
    channel_user_id: str
    user_id: str
    channel_id: str | None = None
    push_enabled: bool = False

    def __post_init__(self) -> None:
        channel_id = self.make_channel_id(self.channel_type, self.channel_user_id)
        if self.channel_id is None:
            self.channel_id = channel_id
        else:
            assert self.channel_id == channel_id, \
                'Channel ID does not match the expected format'

    @classmethod
    def make_channel_id(cls, channel_type: ChannelType, channel_user_id: str) -> str:
        return f'{channel_type}:{channel_user_id}'


class UserTable:
    table = boto3.resource('dynamodb', 'us-west-2').Table('secretary_user')

    @classmethod
    def upsert(cls, user: User) -> None:
        cls.table.put_item(Item=asdict(user))

    @classmethod
    def get(cls, user_id: str) -> User:
        try:
            return User(**cls.table.get_item(Key={'user_id': user_id})['Item'])
        except KeyError:
            raise UserDataNotFoundError

    @classmethod
    def delete(cls, user_id: str) -> None:
        cls.table.delete_item(Key={'user_id': user_id})


class OAuthTable:
    table = boto3.resource('dynamodb', 'us-west-2').Table('secretary_oauth')


class ChannelTable:
    table = boto3.resource('dynamodb', 'us-west-2').Table('secretary_channel')

    @classmethod
    def get(cls, channel_id: str) -> Channel:
        try:
            return Channel(**cls.table.get_item(Key={'channel_id': channel_id})['Item'])
        except KeyError:
            raise UserDataNotFoundError

    @classmethod
    def get_channels_for_user_id(cls, user_id: str) -> list[Channel]:
        items = cls.table.query(
            IndexName='user_id-index',
            KeyConditionExpression=Key('user_id').eq(user_id)
        )['Items']

        return [Channel(**item) for item in items]

    @classmethod
    def upsert(cls, channel: Channel) -> None:
        cls.table.put_item(Item=asdict(channel))

    @classmethod
    def delete(cls, user_id: str) -> None:
        channels = cls.table.query(
            IndexName='user_id-index',
            KeyConditionExpression=Key('user_id').eq(user_id)
        )['Items']

        for item in channels:
            cls.table.delete_item(Key={'channel_id': item['channel_id']})


def disconnect_channel(user_id: str) -> None:
    pass
