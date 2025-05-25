import discord
from agents import Runner
from discord import ChannelType
from discord import Message

import secretary
from secretary.config import discord_bot_token
from secretary.agents.main_agent import get_secretary_agent
from secretary.database import NoSuchUserError
from secretary.database import ChannelTable


class SecretaryDiscordBot(discord.Client):
    async def on_message(self, message: Message) -> None:
        if not self.should_reply_to_message(message):
            return

        async with message.channel.typing():
            reply = await self.reply(message)
        if reply:
            await message.channel.send(reply)

    async def reply(self, message: Message) -> str | None:
        try:
            ChannelTable().get('discord', str(message.author.id))
        except NoSuchUserError:
            return self.signup_message(message)

        sb_user_id = ChannelTable().look_up_user_id('discord', str(message.author.id))
        async with get_secretary_agent(sb_user_id) as agent:
            result = await Runner().run(
                agent,
                f"{message.content} (reply in the format of a Discord message)"
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

    def signup_message(self, message: Message) -> str:
        return (
            "Hi! I'm your personal secretary. To get started, link your Google account: "
            f'https://secretary.scooterbot.ai/login?du={message.author.id}&dch={message.channel.id}'
        )


def run():
    secretary.init()

    intents = discord.Intents.default()
    intents.message_content = True

    bot = SecretaryDiscordBot(intents=intents)
    bot.run(discord_bot_token())


if __name__ == '__main__':
    run()
