from typing import cast

import textwrap

from agents import function_tool
from googleapiclient import discovery

from secretary.service_config import config
from secretary.agents.account_administration_agent import AccountAdministrationAgent
from secretary.agents.base import BaseSecretaryAgent
from secretary.agents.base import UserContext
from secretary.agents.base import UserContextWrapper
from secretary.agents.calendar_agent import CalendarAgent
from secretary.agents.house_agent import HouseAgent
from secretary.agents.tesla_agent import TeslaAgent
from secretary.agents.todo_agent import TodoAgent
from secretary.google_apis import get_google_apis_creds


class SecretaryAgent(BaseSecretaryAgent):
    def __init__(self, user_ctx: UserContext) -> None:
        calendar_agent = CalendarAgent(
            calsvc=discovery.build('calendar', 'v3', credentials=get_google_apis_creds(user_ctx.user_id)),
            gmaps_api_key=config.google_apis.api_key,
        )

        todo_agent = TodoAgent(
            calsvc=discovery.build('calendar', 'v3', credentials=get_google_apis_creds(user_ctx.user_id)),
            gmaps_api_key=config.google_apis.api_key,
        )

        tools = [
            calendar_agent.as_tool(
                tool_name='read_and_manage_calendars_with_calendar_agent',
                tool_description="The Calendar Agent can search and create events across the user's Google Calendars.",
            ),
            todo_agent.as_tool(
                tool_name='read_and_manage_todos_with_todo_agent',
                tool_description="The Todo Agent can search, create, and resolve todos on the user's todo list.",
            ),
        ]

        if user_ctx.tesla_user_id:
            tools += [
                make_request_to_tesla_agent,
            ]

        if user_ctx.house_user_id:
            tools += [
                make_request_to_house_agent,
            ]

        super().__init__(
            name=self.__class__.__name__,
            model='gpt-4.1',
            instructions=self.agent_app_context() + textwrap.dedent(
                '''\
                # Role

                You are the main agent responsible for responding to user requests

                # Instructions

                Carry out requests using the provided tools.

                ## Guidelines

                ### Tools and Delegation to Other Agents

                - If request can be fulfilled using a provided tool, you MUST use that tool and
                  respond according to the tool's output. Never attempt to answer the these these
                  requests without using the tool.

                - If request is about subscriptions, payments, account linking, or account removal,
                  you MUST call the hand-off tool `transfer_to_accountadministration_agent` and then
                  stop. Never attempt to answer these topics yourself.

                - When using tools and delegation, always make a fresh call. NEVER assume a call
                  from a prior conversation turn is still valid.

                - If you cannot complete a task using the tools, ask the user for more information
                  or clarification, or tell them you cannot complete the task. Never just make up
                  information.

                - Only consider a task complete if you get a successful response from the relevant
                  tools.
                '''
            ),
            output_type=str,
            tools=tools,
            handoffs=[
                AccountAdministrationAgent(user_ctx),
            ],
        )


@function_tool
async def make_request_to_tesla_agent(ctx: UserContextWrapper, request_in_natural_language: str) -> str:
    """The Tesla Agent can respond to requests about the locations of the user's Tesla vehicles,
    send navigation requests to them, and more.
    """
    user_ctx = cast(UserContext, ctx.context)

    assert user_ctx.tesla_user_id

    return await TeslaAgent(user_ctx.tesla_user_id).make_request(request_in_natural_language)


@function_tool
async def make_request_to_house_agent(ctx: UserContextWrapper, request_in_natural_language: str) -> str:
    """The House Agent can respond to requests about the status of the user's smart home
    """
    user_ctx = cast(UserContext, ctx.context)

    assert user_ctx.house_user_id

    return await HouseAgent(user_ctx.house_user_id).make_request(request_in_natural_language)
