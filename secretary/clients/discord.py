import httpx
import staticconf


def bot_token() -> str:
    return staticconf.read('discord.bot_token', namespace='secretary')  # type: ignore


async def say(content: str, channel: str) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(
            f'https://discord.com/api/channels/{channel}/messages',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bot {bot_token()}',
            },
            json={'content': content},
        )
