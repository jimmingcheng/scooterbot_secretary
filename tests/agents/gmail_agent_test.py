from __future__ import annotations

import asyncio
from unittest.mock import call
from unittest.mock import patch
from unittest.mock import sentinel

import pytest
from agents import function_tool
from agents import Runner

from secretary.agents.base import UserContext
from secretary.agents.base import UserContextWrapper
from secretary.agents.gmail_agent import GmailAgent
from secretary.data_models.gmail_thread import GmailThreadsResult
from tests.agents.gmail_agent_query_expansion import get_query_expansions
from tests.conftest import ToolCallTracker


TOOL_CALLS = ToolCallTracker()
TEST_TZ = 'America/New_York'


@function_tool
async def search_message_threads(
    ctx: UserContextWrapper,
    keywords: str,
    sender: str | None = None,
    include_threads_older_than_2y: bool = False,
) -> GmailThreadsResult:
    TOOL_CALLS.add(
        call.search_message_threads(
            sentinel.ctx,
            keywords,
            sender=sender,
            include_threads_older_than_2y=include_threads_older_than_2y,
        )
    )
    return GmailThreadsResult(threads=[])


###################################################################################################


@pytest.fixture(autouse=True)
def mock_all_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr('secretary.agents.gmail_agent.search_message_threads', search_message_threads)


@pytest.fixture(autouse=True)
def mock_calendar_service() -> None:
    with patch('secretary.agents.gmail_agent.get_calendar_service') as mock_func:
        mock_func.return_value.settings.return_value.get.return_value.execute.return_value = {
            'value': TEST_TZ,
        }
        yield mock_func


###################################################################################################


def run_agent(request: str) -> str:
    ctx = UserContext(user_id='test_user_id')

    result = asyncio.run(
        Runner().run(
            GmailAgent(ctx),
            request,
            context=ctx,
        )
    )

    return result.final_output


def _test_search_message_threads(
    request: str,
    expected_keywords: set[str],
    expected_include_threads_older_than_2y: bool = False,
    expected_sender: str | None = None,
) -> None:
    TOOL_CALLS.reset()

    run_agent(request)

    tool_call = TOOL_CALLS.get()[0]

    keywords = tool_call.args[1]

    ok = False
    for actual_keywords in get_query_expansions(keywords):
        if len(actual_keywords) >= 2 and actual_keywords <= expected_keywords:
            ok = True
            break

    assert ok

    assert tool_call.kwargs['sender'] == expected_sender
    assert tool_call.kwargs['include_threads_older_than_2y'] == expected_include_threads_older_than_2y


def test_search_message_threads() -> None:
    _test_search_message_threads(
        "What's my flight to Denver?",
        expected_keywords={'flight', 'denver'},
    )

    _test_search_message_threads(
        "What's my driver's license number?",
        expected_keywords={'driver', 'license'},
        expected_include_threads_older_than_2y=True,
    )

    _test_search_message_threads(
        "Did I get an invite for Joe's birthday party?",
        expected_keywords={'joe', 'birthday', 'party'},
    )

    _test_search_message_threads(
        "What did the Dr. Smith say about my treatment plan?",
        expected_keywords={'dr', 'smith', 'treatment', 'plan'},
        expected_include_threads_older_than_2y=True,
    )
