import boto3
from boto3.resources.base import ServiceResource

from sb_service_util.data_models.channel import ChannelBase


class Channel(ChannelBase):
    @classmethod
    def table(cls) -> ServiceResource:
        return boto3.resource('dynamodb', 'us-west-2').Table('secretary_channel')
