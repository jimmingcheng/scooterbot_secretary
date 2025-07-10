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
from secretary.agents.gmail_agent import Query
from secretary.agents.gmail_agent import QueryType
from secretary.data_models.gmail_thread import GmailThreadsResult
from tests.conftest import ToolCallTracker


TOOL_CALLS = ToolCallTracker()
TEST_TZ = 'America/New_York'


@function_tool
async def search_message_threads(
    ctx: UserContextWrapper,
    query: Query,
    sender: str | None = None,
) -> GmailThreadsResult:
    TOOL_CALLS.add(
        call.search_message_threads(
            sentinel.ctx,
            query,
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
    expected_kw_phrases: list[set[str]],
    expected_query_type: QueryType = 'recent_or_current_events',
    expected_sender: str | None = None,
) -> None:
    TOOL_CALLS.reset()

    run_agent(request)

    tool_call = TOOL_CALLS.get()[0]

    query: Query = tool_call.args[1]

    kw_phrases = []
    for kw_phrase in query.keyword_phrases:
        kw_phrases += [{
            kw.lower().replace("'s", '')
            for kw in kw_phrase.unordered_keywords
        }]

    test_pairs = [
        (kw_phrase, expected_kw_phrase)
        for kw_phrase in kw_phrases
        for expected_kw_phrase in expected_kw_phrases
    ]

    assert any(
        kw_phrase and kw_phrase <= expected_kw_phrase
        for kw_phrase, expected_kw_phrase in test_pairs
    ), f'input `{str(query)}` did not resolve to one of the expected keyword phrases `{expected_kw_phrases}`'

    assert query.query_type == expected_query_type
    assert query.sender == expected_sender


def test_search_message_threads() -> None:
    _test_search_message_threads(
        "When's my flight to Denver?",
        [{'flight', 'denver'}],
    )

    _test_search_message_threads(
        "What's my driver's license number?",
        [
            {'driver', 'license'},
            {'driver license'},
        ],
        expected_query_type='records_lookup',
    )

    _test_search_message_threads(
        "Did I receive an invitation for Joe's birthday party?",
        [{'joe', 'birthday', 'party', 'invitation'}],
    )

    _test_search_message_threads(
        "What's the EIN for Bob's Bakery?",
        [
            {'ein', 'bob bakery'},
            {'employer', 'identification', 'number', 'bob bakery'},
            {'ein', 'bob', 'bakery'},
            {'employer', 'identification', 'number', 'bob', 'bakery'},
        ],
        expected_query_type='records_lookup',
    )
