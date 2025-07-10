from __future__ import annotations

from typing import cast
from typing import Literal

import arrow
import textwrap
from agents import Agent as OpenAIAgent
from agents import function_tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from pydantic import BaseModel

from secretary.agents.base import UserContext
from secretary.agents.base import UserContextWrapper
from secretary.data_models.gmail_thread import GmailThread, GmailThreadsResult
from secretary.google_apis import get_calendar_service


QueryType = Literal['recent_or_current_events', 'records_lookup']


class KeywordPhrase(BaseModel):
    unordered_keywords: list[str]


class Query(BaseModel):
    query_type: QueryType = 'recent_or_current_events'
    keyword_phrases: list[KeywordPhrase] = []
    sender: str | None = None

    def __str__(self) -> str:
        query_str = ' OR '.join(
            '(' + ' '.join(phrase.unordered_keywords) + ')'
            for phrase in self.keyword_phrases
        )
        if self.query_type == 'records_lookup':
            query_str += ' after:' + arrow.now().shift(years=-2).format('YYYY-MM-DD')
        if self.sender:
            query_str += f' from:{self.sender}'
        return query_str


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

                ### Keyword Phrases

                A keyword is a single term, such as "bob", "flight", or "social security". Most
                keywords are single words, but they can also multiple words separated by spaces
                (ordered).

                A keyword phrase is an unordered set of keywords that must all occur together, such
                as {{"dentist", "arlington"}} or {{"honda", "license plate"}}.
                thread only if all terms are present.

                #### Choose Keyword Phrases that Balance Recall and Precision

                What's my car's license plate number?
                - BAD: ["license", "plate", "number"] (loses recall without adding much precision)
                - GOOD: ["license", "plate"]
                - GOOD: ["license plate"]

                What was the name of the dentist I saw in Arlington?
                - BAD: ["dentist", "in", "arlington"] (unnecessary preposition)
                - GOOD: ["dentist", "arlington"]

                What's my social security number?
                - BAD: ["ssn", "social security"] (redundant terms in single keyword phrase)
                - GOOD: ["ssn"]
                - GOOD: ["social security"]

                #### Add Keyword Phrases to Expand Synonyms

                Generate up to 4 different keyword phrases to help recall

                What's my social security number?
                - ["ssn"]
                - ["social security"]

                What's my itinerary for Boston?
                - ["trip", "boston"]
                - ["itinerary", "boston"]
                - ["flight", "boston"]

                ### Senders

                Examples:

                - Bob Jones
                - jim@abc.com
                - amazon.com

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
    query: Query,
) -> GmailThreadsResult:
    """
    query_type: Set this to True to look up historical records likely to be
      found in threads older than 2 years. Most routine activities should not require this.
    """
    user_id = cast(UserContext, ctx.context).user_id

    return GmailThread.search(
        user_id=user_id,
        query=str(query),
        label_ids=[],
    )
