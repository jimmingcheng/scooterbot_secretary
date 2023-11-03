import requests
import staticconf


def bot_token() -> str:
    return staticconf.read('discord.bot_token', namespace='secretary')  # type: ignore


def say(content: str, channel: str) -> None:
    requests.post(
        f'https://discord.com/api/channels/{channel}/messages',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bot {bot_token()}',
        },
        json={'content': content},
    )
