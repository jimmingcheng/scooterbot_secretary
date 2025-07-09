import os

import openai

import secretary.service_config
import secretary.logger
from secretary.service_config import cfg


def init(config_path: str = '/sb/config/secretary.yaml') -> None:
    secretary.service_config.config_path = config_path

    openai_api_key = os.environ.get('OPENAI_API_KEY') or cfg().openai_api_key
    openai.api_key = openai_api_key
    os.environ['OPENAI_API_KEY'] = openai_api_key

    secretary.logger.init()
