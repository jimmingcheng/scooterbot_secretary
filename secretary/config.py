import openai
import os
import staticconf


def load_all_configs() -> None:
    load_todo_config()
    load_openai()


def load_todo_config() -> None:
    staticconf.YamlConfiguration('/sb/config/secretary.yaml', namespace='secretary')
    openai.api_key = staticconf.read('openai_api_key', namespace='secretary')  # type: ignore


def load_openai() -> None:
    openai.api_key = staticconf.read('openai_api_key', namespace='secretary')  # type: ignore
    os.environ['OPENAI_API_KEY'] = openai.api_key  # type: ignore


def google_api_key() -> str:
    return staticconf.read('google_apis.api_key', namespace='secretary')  # type: ignore


def discord_bot_token() -> str:
    return staticconf.read('discord.bot_token', namespace='secretary')  # type: ignore
