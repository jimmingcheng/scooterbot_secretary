from typing import AsyncIterator

import textwrap
from agents import Agent as OpenAIAgent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.mcp import MCPServer
from agents.mcp import MCPServerStreamableHttp
from calendar_agent import CalendarAgent
from contextlib import asynccontextmanager
from contextlib import AsyncExitStack
from googleapiclient import discovery

from secretary.google_apis import get_google_apis_creds
from secretary.config import google_api_key


class SecretaryAgent(OpenAIAgent):
    def __init__(
        self,
        user_id: str,
        house_mcp_server: MCPServer,
        tesla_mcp_server: MCPServer,
        tesla_user_id: str,
    ) -> None:
        calendar_agent = CalendarAgent(
            calsvc=discovery.build('calendar', 'v3', credentials=get_google_apis_creds(user_id)),
            gmaps_api_key=google_api_key(),
        )

        super().__init__(
            name=self.__class__.__name__,
            model='gpt-4.1',
            instructions=RECOMMENDED_PROMPT_PREFIX + '\n\n' + textwrap.dedent(
                '''\
                # Instructions

                You are a personal secretary for the user. You have tools to read and manage their:

                - personal and other calendars
                - cars via the Tesla API
                - smart home via an API

                Use these tools to help the user with their requests. Always use the tools to get
                the most accurate and up-to-date information. If you cannot complete a task using
                the tools, ask the user for more information or clarification, or tell them you
                cannot complete the task. Never just make up information. Only consider a task
                complete if you get a successful response from the relevant tools.

                ## tesla_user_id

                {tesla_user_id}
                '''
            ).format(
                tesla_user_id=tesla_user_id,
            ),
            output_type=str,
            mcp_servers=[
                house_mcp_server,
                tesla_mcp_server,
            ],
            tools=[
                calendar_agent.as_tool(
                    tool_name='read_and_manage_calendars',
                    tool_description='Search for or create calendar events.',
                ),
            ],
        )


@asynccontextmanager
async def get_secretary_agent(user_id: str) -> AsyncIterator[SecretaryAgent]:
    async with AsyncExitStack() as stack:
        mcp_server_configs = [
            ('house', 'http://house_mcp:9888/mcp'),
            ('tesla', 'http://tesla_mcp:9888/mcp'),
        ]
        mcp_servers = [
            await stack.enter_async_context(
                MCPServerStreamableHttp(name=name, params={'url': url})
            )
            for name, url in mcp_server_configs
        ]

        yield SecretaryAgent(
            user_id=user_id,
            house_mcp_server=mcp_servers[0],
            tesla_mcp_server=mcp_servers[1],
            tesla_user_id='ba813a80-54b6-4ca3-8d55-f964d2145b4b',
        )
