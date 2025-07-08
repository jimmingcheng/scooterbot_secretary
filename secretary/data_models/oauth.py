import boto3
from boto3.resources.base import ServiceResource


class SecretaryOAuth:
    @classmethod
    def table(cls) -> ServiceResource:
        return boto3.resource('dynamodb', 'us-west-2').Table('secretary_oauth')

    @classmethod
    def delete(cls, user_id: str) -> None:
        cls.table().delete_item(Key={'user_id': user_id})
