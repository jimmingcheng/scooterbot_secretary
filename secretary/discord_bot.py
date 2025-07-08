from typing import Any

import arrow
import discord
from agents import Runner
from discord import ChannelType
from discord import Message
from sb_service_util.errors import UserDataNotFoundError

import secretary
from secretary.agents.main_agent import SecretaryAgent
from secretary.service_config import config
from secretary.data_models import Channel


class SecretaryDiscordBot(discord.Client):
    async def on_message(self, message: Message) -> None:
        if not self.should_reply_to_message(message):
            return

        async with message.channel.typing():
            reply = await self.reply(message)
        if reply:
            await message.channel.send(reply)

    async def reply(self, message: Message) -> str | None:
        messages = await self.get_convo_history_for_openai(message.channel)

        messages += [
            {'role': 'user', 'content': f'{message.content} (reply in the format of a Discord message)'},
        ]

        try:
            sb_user_id = Channel.get('discord', str(message.author.id)).user_id
        except UserDataNotFoundError:
            return self.signup_message(message)

        user_ctx = SecretaryAgent.get_user_context(sb_user_id)

        result = await Runner().run(
            SecretaryAgent(user_ctx),
            input=messages,  # type: ignore
            context=user_ctx,
        )

        return result.final_output

    def monitored_channels(self) -> list[int]:
        return []

    def should_reply_to_message(self, message: Message) -> bool:
        if message.author == self.user:
            # Never reply to self, to avoid infinite loops
            return False
        elif message.channel.type == ChannelType.private:
            return True
        elif self.user in message.mentions:
            return True
        elif all([
            message.channel.id in self.monitored_channels(),
            not message.mentions,
            not message.author.bot,
        ]):
            return True
        else:
            return False

    async def get_convo_history_for_openai(self, channel: Any) -> list[dict[str, str]]:
        five_minutes_ago = arrow.utcnow().shift(minutes=-5)

        openai_messages = []
        async for msg in channel.history(limit=20, oldest_first=False):
            if arrow.get(msg.created_at) < five_minutes_ago:
                continue
            elif msg.author == self.user:
                openai_messages += [{'role': 'assistant', 'content': msg.content}]
            elif self.should_reply_to_message(msg):
                openai_messages += [{'role': 'user', 'content': msg.content}]

        openai_messages.reverse()

        return openai_messages

    def signup_message(self, message: Message) -> str:
        return (
            "Hi! I'm your personal secretary. To get started, link your Google account: "
            f'https://secretary.scooterbot.ai/setup?du={message.author.id}'
        )


def run():
    import logging
    logging.info('Starting Secretary Discord Bot...')
    secretary.init()

    intents = discord.Intents.default()
    intents.message_content = True

    bot = SecretaryDiscordBot(intents=intents)
    bot.run(config.discord.bot_token)


if __name__ == '__main__':
    run()
