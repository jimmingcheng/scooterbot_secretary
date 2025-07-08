import httpx


from secretary.service_config import config
from secretary.data_models import SecretaryChannel


async def say(
    content: str,
    user_id: str,
) -> None:
    discord_user_id = None
    for channel in SecretaryChannel.get_channels_for_user_id(user_id):
        if channel.channel_type == 'discord':
            discord_user_id = channel.channel_user_id

    assert discord_user_id, 'Discord is not an available channel for this user.'

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            'https://discord.com/api/users/@me/channels',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bot {config.discord.bot_token}',
            },
            json={'recipient_id': discord_user_id},
        )

        channel = resp.json()['id']

        await client.post(
            f'https://discord.com/api/channels/{channel}/messages',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bot {config.discord.bot_token}',
            },
            json={'content': content},
        )
