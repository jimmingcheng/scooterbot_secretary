import httpx

from sb_service_util.data_models.channel import ChannelType

from secretary.service_config import config
from secretary.data_models import SecretaryChannel


async def notify(user_id: str, message: str, channel_type: ChannelType | None = None) -> None:
    channels_to_notify = get_channels_to_notify(user_id)

    if channel_type:
        channels_to_notify = [ch for ch in channels_to_notify if ch.channel_type == channel_type]

    for channel in channels_to_notify:
        if channel.channel_type == 'discord':
            await discord_notify(discord_user_id=channel.channel_user_id, message=message)


async def discord_notify(discord_user_id: str, message: str) -> None:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            'https://discord.com/api/users/@me/channels',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bot {config.discord.bot_token}'
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
            json={'content': message},
        )


def get_channels_to_notify(user_id: str) -> list[SecretaryChannel]:
    return [
        ch for ch in SecretaryChannel.get_channels_for_user_id(user_id)
        if ch.push_enabled
    ]
