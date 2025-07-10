from __future__ import annotations
from typing import Any

import asyncio
from unittest.mock import call
from unittest.mock import patch
from unittest.mock import sentinel

import arrow
import pytest
from agents import function_tool
from agents import Runner

from secretary.agents.base import UserContext
from secretary.agents.base import UserContextWrapper
from secretary.agents.calendar_agent import CalendarAgent
from secretary.agents.calendar_agent import EventsResult
from tests.conftest import ToolCallTracker


TOOL_CALLS = ToolCallTracker()
TEST_TZ = 'America/New_York'
NOW = arrow.now(TEST_TZ)


@function_tool
async def search_events(
    ctx: UserContextWrapper,
    calendar_id: str,
    time_min: str,
    time_max: str,
) -> EventsResult:
    TOOL_CALLS.add(
        call.search_events(
            sentinel.ctx,
            calendar_id,
            time_min,
            time_max,
        )
    )
    return EventsResult(events=[])


###################################################################################################


@pytest.fixture(autouse=True)
def mock_all_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr('secretary.agents.calendar_agent.search_events', search_events)


@pytest.fixture(autouse=True)
def mock_calendar_service() -> None:
    with patch('secretary.agents.calendar_agent.get_calendar_service') as mock_func:
        mock_func.return_value.settings.return_value.get.return_value.execute.return_value = {
            'value': TEST_TZ,
        }

        mock_func.return_value.calendarList.return_value.list.return_value.execute.return_value = {
            'items': [
                {
                    'id': 'primary_calendar_id',
                    'summary': 'Personal',
                    'primary': True,
                },
                {
                    'id': 'work_calendar_id',
                    'summary': 'Work',
                },
                {
                    'id': 'medical_calendar_id',
                    'summary': 'Medical',
                },
            ],
        }
        yield mock_func


###################################################################################################


def run_agent(request: str) -> str:
    ctx = UserContext(user_id='test_user_id')

    result = asyncio.run(
        Runner().run(
            CalendarAgent(ctx),
            request,
            context=ctx,
        )
    )

    return result.final_output


def _test_search_events(
    request: str,
    expected_calls: list[Any],
    expected_max_time_diff_days: int,
) -> None:
    TOOL_CALLS.reset()

    run_agent(request)

    actual_calls = TOOL_CALLS.get()

    test_pairs = [
        (actual_call, expected_call)
        for actual_call in actual_calls
        for expected_call in expected_calls
    ]

    def is_similar(actual: Any, expected: Any) -> bool:
        _, actual_calendar_id, actual_time_min, actual_time_max = actual.args
        _, expected_calendar_id, expected_time_min, expected_time_max = expected.args

        if actual_calendar_id != expected_calendar_id:
            return False

        time_diff_days = abs((arrow.get(actual_time_min) - arrow.get(expected_time_min)).days)

        return time_diff_days <= expected_max_time_diff_days

    assert any(
        is_similar(actual, expected) for actual, expected in test_pairs
    ), f'Actual calls {actual_calls} did not match expected calls {expected_calls}'


def test_search_events() -> None:
    _test_search_events(
        request="What's on my calendar for the next 7 days?",
        expected_calls=[
            call.search_events(
                sentinel.ctx,
                'primary_calendar_id',
                NOW.isoformat(),
                NOW.shift(days=7).isoformat(),
            ),
        ],
        expected_max_time_diff_days=1,
    )

    _test_search_events(
        request="What's on my work calendar for the next 7 days?",
        expected_calls=[
            call.search_events(
                sentinel.ctx,
                'work_calendar_id',
                NOW.isoformat(),
                NOW.shift(days=7).isoformat(),
            ),
        ],
        expected_max_time_diff_days=1,
    )

    _test_search_events(
        request="What did my doctor say about my knee last year?",
        expected_calls=[
            call.search_events(
                sentinel.ctx,
                'primary_calendar_id',
                NOW.shift(years=-1).isoformat(),
                NOW.isoformat(),
            ),
            call.search_events(
                sentinel.ctx,
                'medical_calendar_id',
                NOW.shift(years=-1).isoformat(),
                NOW.isoformat(),
            ),
        ],
        expected_max_time_diff_days=365,
    )

    _test_search_events(
        request="When was my last haircut?",
        expected_calls=[
            call.search_events(
                sentinel.ctx,
                'primary_calendar_id',
                NOW.shift(years=-1).isoformat(),
                NOW.isoformat(),
            ),
        ],
        expected_max_time_diff_days=270,
    )
