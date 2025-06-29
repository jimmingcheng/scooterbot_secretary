import os

import openai

from secretary import logger


def init() -> None:
    from secretary.service_config import config

    openai_api_key = os.environ.get('OPENAI_API_KEY') or config.openai_api_key
    openai.api_key = openai_api_key
    os.environ['OPENAI_API_KEY'] = openai_api_key

    logger.init()
