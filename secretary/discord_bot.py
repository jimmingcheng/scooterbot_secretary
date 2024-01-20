from typing import Optional

import asyncio
import discord
import staticconf
from discord import Message
from llm_discord_bot.bot import LLMDiscordBot
from llm_task_handler.dispatch import TaskDispatcher

import secretary
from secretary.database import NoSuchUserError
from secretary.database import ChannelTable
from secretary.tasks.account import DisconnectAccount
from secretary.tasks.calendar import AddCalendarEventFromDiscord
from secretary.tasks.question import AnswerQuestionFromCalendar
from secretary.tasks.todo import AddTodoFromDiscord


class SecretaryDiscordBot(LLMDiscordBot):
    def bot_token(self) -> str:
        return staticconf.read('discord.bot_token', namespace='secretary')  # type: ignore

    def prompt_task_dispatcher(self, user_id: str) -> TaskDispatcher:
        return TaskDispatcher([
        ])

    def conversation_task_dispatcher(self, user_id: str) -> TaskDispatcher:
        sb_user_id = ChannelTable().look_up_user_id('discord', user_id)
        return TaskDispatcher([
            AnswerQuestionFromCalendar(user_id=sb_user_id),
            AddCalendarEventFromDiscord(user_id=sb_user_id),
            AddTodoFromDiscord(user_id=sb_user_id),
            DisconnectAccount(user_id=sb_user_id),
        ])

    def monitored_channels(self) -> list[int]:
        return []

    async def reply(self, message: Message) -> Optional[str]:
        try:
            user_id = str(message.author.id)
            ChannelTable().get('discord', user_id)
        except NoSuchUserError:
            return self.signup_message(message)

        try:
            return await asyncio.wait_for(super().reply(message), timeout=20) or '🤷'
        except asyncio.TimeoutError:
            return '🤷 timeout'

    def signup_message(self, message: Message) -> str:
        return (
            "Hi! I'm your personal secretary. To get started, link your Google account: "
            f'https://secretary.scooterbot.ai/login?u={message.author.id}&ch={message.channel.id}'
        )


def run():
    secretary.init()

    intents = discord.Intents.default()
    intents.message_content = True

    bot = SecretaryDiscordBot(command_prefix='$', intents=intents)
    bot.run(bot.bot_token())


if __name__ == '__main__':
    run()
