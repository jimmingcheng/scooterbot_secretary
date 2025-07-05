from typing import cast

import textwrap

from agents import function_tool
from calendar_agent import CalendarAgent
from googleapiclient import discovery

from secretary.service_config import config
from secretary.account_linking import get_account_link_manager
from secretary.agents.base import BaseSecretaryAgent
from secretary.agents.base import UserContext
from secretary.agents.base import UserContextWrapper
from secretary.agents.house_agent import HouseAgent
from secretary.agents.tesla_agent import TeslaAgent
from secretary.google_apis import get_google_apis_creds


class SecretaryAgent(BaseSecretaryAgent):
    def __init__(self, user_ctx: UserContext) -> None:
        calendar_agent = CalendarAgent(
            calsvc=discovery.build('calendar', 'v3', credentials=get_google_apis_creds(user_ctx.user_id)),
            gmaps_api_key=config.google_apis.api_key,
        )

        tools = [
            calendar_agent.as_tool(
                tool_name='read_and_manage_calendars_with_calendar_agent',
                tool_description="The Calendar Agent can search and create events across the user's Google Calendars.",
            ),
        ]

        if user_ctx.tesla_user_id:
            tools += [
                make_request_to_tesla_agent,
            ]
        else:
            tools += [
                link_account_to_tesla_agent,
            ]

        if user_ctx.house_user_id:
            tools += [
                make_request_to_house_agent,
            ]
        else:
            tools += [
                link_account_to_house_agent,
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

                ### Tool Use

                - If request can be fulfilled using a provided tool, you MUST use that tool and
                  respond according to the tool's output. Never attempt to answer the these these
                  requests without using the tool.

                - When using tools and delegation, always make a fresh call. Don't assume a call
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


@function_tool
async def link_account_to_tesla_agent(ctx: UserContextWrapper) -> str:
    user_ctx = cast(UserContext, ctx.context)
    token = get_account_link_manager().make_token('secretary', user_ctx.user_id)
    url = config.account_links.tesla.linking_url + '?a=secretary&u=' + user_ctx.user_id + '&t=' + token
    return 'To link your Secretary Agent with your Tesla Agent, visit: ' + url


@function_tool
async def link_account_to_house_agent(ctx: UserContextWrapper) -> str:
    user_ctx = cast(UserContext, ctx.context)
    token = get_account_link_manager().make_token('secretary', user_ctx.user_id)
    url = config.account_links.house.linking_url + '?a=secretary&u=' + user_ctx.user_id + '&t=' + token
    return 'To link your Secretary Agent with your House Agent, visit: ' + url
