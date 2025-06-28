import openai
import os
import staticconf


def load_all_configs() -> None:
    load_todo_config()
    load_openai()


def _config_read(key: str) -> str:
    return staticconf.read(key, namespace='secretary')  # type: ignore


def load_todo_config() -> None:
    staticconf.YamlConfiguration('/sb/config/secretary.yaml', namespace='secretary')


def load_openai() -> None:
    openai.api_key = _config_read('openai_api_key')
    os.environ['OPENAI_API_KEY'] = openai.api_key


def google_api_key() -> str:
    return _config_read('google_apis.api_key')


def discord_bot_token() -> str:
    return _config_read('discord.bot_token')


def account_linking_shared_secret() -> str:
    return _config_read('account_linking.shared_secret')


def account_linking_tesla_url() -> str:
    return _config_read('account_linking.tesla_url')


def tesla_private_api_host() -> str:
    return _config_read('tesla_private_api_host')
