from __future__ import annotations

from typing import cast

import arrow
import textwrap
from agents import Agent as OpenAIAgent
from agents import function_tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from secretary.agents.base import UserContext
from secretary.agents.base import UserContextWrapper
from secretary.data_models.gmail_thread import GmailThread, GmailThreadsResult
from secretary.google_apis import get_calendar_service


class GmailAgent(OpenAIAgent):
    def __init__(
        self,
        user_ctx: UserContext,
        model: str = 'gpt-4.1',
    ) -> None:
        calsvc = get_calendar_service(user_ctx.user_id)
        user_tz = calsvc.settings().get(setting='timezone').execute().get('value')
        super().__init__(
            name=self.__class__.__name__,
            model=model,
            instructions=RECOMMENDED_PROMPT_PREFIX + '\n\n' + textwrap.dedent(
                '''\
                # Instructions

                Use the provided tools to answer questions based on information from message
                threads in the user's Gmail account.

                ## Guidelines

                ### Keywords for Searching Threads

                Choose keywords to carefully balance recall and precision while using this syntax:

                - Parentheses = group terms
                - Space = all terms must be present
                - OR = logical OR
                - Strip all punctuation

                #### Good Examples

                - `What's my car's license plate number?` -> `license plate`
                - `What was the name of the dentist I saw in Arlington?` -> `dentist arlington`
                - `What's my itinerary for Boston?` -> `(trip OR itinerary OR flight) boston`

                #### Bad Examples

                - `license plate number` ("number" unnecessarily reduces recall without adding much precision)
                - `itinerary boston` (itinerary is a rather specific term, could use OR expansion)

                ### Date Ranges

                If the question is about a personal record, or something my require looking back
                in very old records, set `date_min` to 1970-01-01

                # Current Time & Time Zone

                {current_time}

                ''',
            ).format(
                current_time=arrow.now(user_tz).isoformat(),
            ),
            output_type=str,
            tools=[
                search_message_threads,
            ],
        )


@function_tool
async def search_message_threads(
    ctx: UserContextWrapper,
    keywords: str,
    sender: str | None = None,
    include_threads_older_than_2y: bool = False,
) -> GmailThreadsResult:
    """
    sender: Examples: `"Bob Jones"`, `amazon.com`, `jim@abc.com`
    include_threads_older_than_2y: Set this to True to look up historical records likely to be
      found in threads older than 2 years. Most routine activities should not require this.
    """
    user_id = cast(UserContext, ctx.context).user_id
    calsvc = get_calendar_service(user_id)
    user_tz = calsvc.settings().get(setting='timezone').execute().get('value')

    query = keywords

    if not include_threads_older_than_2y:
        query += ' after:' + arrow.now(user_tz).shift(years=-2).format('YYYY-MM-DD')

    if sender:
        query += f' from:{sender}'

    return GmailThread.search(
        user_id=user_id,
        query=query,
        label_ids=[],
    )
