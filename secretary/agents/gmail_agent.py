from __future__ import annotations

from typing import cast

import textwrap
from agents import Agent as OpenAIAgent
from agents import function_tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from secretary.agents.base import UserContext
from secretary.agents.base import UserContextWrapper
from secretary.data_models.gmail_thread import GmailThread, GmailThreadsResult


class GmailAgent(OpenAIAgent):
    def __init__(
        self,
        user_ctx: UserContext,
        model: str = 'gpt-4.1',
    ) -> None:
        super().__init__(
            name=self.__class__.__name__,
            model=model,
            instructions=RECOMMENDED_PROMPT_PREFIX + '\n\n' + textwrap.dedent(
                '''\
                # Instructions

                Use the provided tools to answer questions based on information from message
                threads in the user's Gmail account.
                ''',
            ),
            output_type=str,
            tools=[
                search_threads,
            ],
        )


@function_tool
async def search_threads(
    ctx: UserContextWrapper,
    keywords: str,
    date_min: str | None = None,
    date_max: str | None = None,
    sender: str | None = None,
) -> GmailThreadsResult:
    """
    keywords: Examples: `"license plate"` (exact match), `dental arlington` (AND), `dental OR dentist` (OR)
    date_min and date_max: YYYY-MM-DD
    sender: Examples: `"Bob Jones"`, `amazon.com`
    """

    parts = [keywords]
    if date_min:
        parts += [f'after:{date_min}']
    if date_max:
        parts += [f'before:{date_max}']
    if sender:
        parts += [f'from:{sender}']

    query = ' '.join(parts).strip()

    user_id = cast(UserContext, ctx.context).user_id

    return GmailThread.search(
        user_id=user_id,
        query=query,
        label_ids=[],
    )
