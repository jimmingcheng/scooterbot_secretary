from typing import cast

import textwrap

from agents import function_tool
from agents import ModelSettings

from secretary.service_config import config
from secretary.account_linking import get_account_link_manager
from secretary.agents.base import BaseSecretaryAgent
from secretary.agents.base import UserContext
from secretary.agents.base import UserContextWrapper


class AccountAdministrationAgent(BaseSecretaryAgent):
    def __init__(self, user_ctx: UserContext) -> None:
        tools = [
            remove_account,
        ]

        if not user_ctx.tesla_user_id:
            tools += [
                link_account_to_tesla_agent,
            ]

        if not user_ctx.house_user_id:
            tools += [
                link_account_to_house_agent,
            ]

        super().__init__(
            name=self.__class__.__name__,
            model='gpt-4.1-mini',
            output_type=str,
            model_settings=ModelSettings(tool_choice='required'),
            tool_use_behavior='stop_on_first_tool',
            tools=tools,  # type: ignore
            handoff_description=textwrap.dedent(
                '''\
                Handle requests relating to subscriptions, payments, account links, and account removal.
                ''',
            ),
            instructions=self.agent_app_context() + textwrap.dedent(
                '''\
                # Role

                Handle requests relating to subscriptions, payments, account links, and account removal.

                # Instructions

                Use one of the tools provided to fulfill the user's request.
                '''
            ),
        )


@function_tool
async def remove_account(ctx: UserContextWrapper) -> str:
    user_ctx = cast(UserContext, ctx.context)
    token = get_account_link_manager().make_token('secretary', user_ctx.user_id)
    url = 'https://secretary.scooterbot.ai/account/remove?u=' + user_ctx.user_id + '&t=' + token
    return f'To remove your account, visit: {url}'


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


@function_tool
async def no_suitable_tool_for_request() -> str:
    return "Sorry, I can't help with this request."
