from __future__ import annotations

from pydantic import BaseModel

import boto3
from boto3.resources.base import ServiceResource


class User(BaseModel):
    user_id: str

    @classmethod
    def table(cls) -> ServiceResource:
        return boto3.resource('dynamodb', 'us-west-2').Table('secretary_user')

    @classmethod
    def list(cls) -> list[User]:
        resp = cls.table().scan()
        users = [User(**item) for item in resp.get('Items', [])]

        while 'LastEvaluatedKey' in resp:
            resp = cls.table().scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
            users += [User(**item) for item in resp.get('Items', [])]

        return users

    @classmethod
    def upsert(cls, user: User) -> None:
        cls.table().put_item(Item=user.model_dump())

    @classmethod
    def delete(cls, user_id: str) -> None:
        cls.table().delete_item(Key={'user_id': user_id})
