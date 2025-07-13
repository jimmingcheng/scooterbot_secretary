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
from tests.conftest import get_next_weekday
from tests.conftest import ToolCallTracker


TOOL_CALLS = ToolCallTracker()
TEST_TZ = 'America/New_York'
NOW = arrow.now(TEST_TZ)


@function_tool
async def list_events(
    ctx: UserContextWrapper,
    calendar_id: str,
    time_min: str,
    time_max: str,
) -> EventsResult:
    TOOL_CALLS.add(
        call.list_events(
            sentinel.ctx,
            calendar_id,
            time_min,
            time_max,
        )
    )
    return EventsResult(events=[])


@function_tool
async def create_event(
    ctx: UserContextWrapper,
    calendar_id: str,
    summary: str,
    start: str,
    end: str,
    location: str | None,
    is_all_day_event: bool,
    rfc5545_recurrence_properties: list[str] | None,
    notes: str | None,
) -> str:
    TOOL_CALLS.add(
        call.create_event(
            sentinel.ctx,
            calendar_id,
            summary,
            start,
            end,
            location,
            is_all_day_event,
            rfc5545_recurrence_properties,
            notes,
        )
    )
    return 'Successfully created event'


###################################################################################################


@pytest.fixture(autouse=True)
def mock_all_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr('secretary.agents.calendar_agent.list_events', list_events)
    monkeypatch.setattr('secretary.agents.calendar_agent.create_event', create_event)


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


def _test_list_events(
    request: str,
    expected_calls_any: list[Any],
    expected_max_time_diff_days: int,
) -> None:
    TOOL_CALLS.reset()

    run_agent(request)

    actual_calls = TOOL_CALLS.get()

    test_pairs = [
        (actual_call, expected_call)
        for actual_call in actual_calls
        for expected_call in expected_calls_any
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
    ), f'Actual calls {actual_calls} did not match expected calls {expected_calls_any}'


def test_list_events() -> None:
    _test_list_events(
        request="What's on my calendar for the next 7 days?",
        expected_calls_any=[
            call.list_events(
                sentinel.ctx,
                'primary_calendar_id',
                NOW.isoformat(),
                NOW.shift(days=7).isoformat(),
            ),
        ],
        expected_max_time_diff_days=1,
    )

    _test_list_events(
        request="What's on my work calendar for the next 7 days?",
        expected_calls_any=[
            call.list_events(
                sentinel.ctx,
                'work_calendar_id',
                NOW.isoformat(),
                NOW.shift(days=7).isoformat(),
            ),
        ],
        expected_max_time_diff_days=1,
    )

    _test_list_events(
        request="What did my doctor say about my knee last year?",
        expected_calls_any=[
            call.list_events(
                sentinel.ctx,
                'primary_calendar_id',
                NOW.shift(years=-1).isoformat(),
                NOW.isoformat(),
            ),
            call.list_events(
                sentinel.ctx,
                'medical_calendar_id',
                NOW.shift(years=-1).isoformat(),
                NOW.isoformat(),
            ),
        ],
        expected_max_time_diff_days=365,
    )

    _test_list_events(
        request="When was my last haircut?",
        expected_calls_any=[
            call.list_events(
                sentinel.ctx,
                'primary_calendar_id',
                NOW.shift(years=-1).isoformat(),
                NOW.isoformat(),
            ),
        ],
        expected_max_time_diff_days=270,
    )


def _test_create_event(
    request: str,
    expected_calls_any: list[Any],
    expected_max_time_diff_days: int,
) -> None:
    TOOL_CALLS.reset()

    run_agent(request)

    actual_calls = TOOL_CALLS.get()

    test_pairs = [
        (actual_call, expected_call)
        for actual_call in actual_calls
        for expected_call in expected_calls_any
    ]

    def is_similar(actual: Any, expected: Any) -> bool:
        (
            _,
            actual_calendar_id,
            actual_summary,
            actual_start,
            actual_end,
            actual_location,
            actual_is_all_day_event,
            actual_rfc5545_recurrence_properties,
            actual_notes,
        ) = actual.args

        (
            _,
            expected_calendar_id,
            expected_summary,
            expected_start,
            expected_end,
            expected_location,
            expected_is_all_day_event,
            expected_rfc5545_recurrence_properties,
            expected_notes,
        ) = expected.args

        if actual_calendar_id != expected_calendar_id:
            return False

        if abs((arrow.get(actual_start) - arrow.get(expected_start)).days) > expected_max_time_diff_days:
            return False

        if abs((arrow.get(actual_end) - arrow.get(expected_end)).days) > expected_max_time_diff_days:
            return False

        if actual_location != expected_location:
            return False

        if actual_is_all_day_event != expected_is_all_day_event:
            return False

        if actual_rfc5545_recurrence_properties != expected_rfc5545_recurrence_properties:
            return False

        if bool(actual_notes) != bool(expected_notes):
            return False

        return True

    assert any(
        is_similar(actual, expected) for actual, expected in test_pairs
    ), f'Actual calls {actual_calls} did not match expected calls {expected_calls_any}'


def test_create_event() -> None:
    _test_create_event(
        request='Schedule dentist appointment on Monday at 3-4 pm',
        expected_calls_any=[
            call.create_event(
                sentinel.ctx,
                'primary_calendar_id',
                'Dentist Appointment',
                get_next_weekday(0, TEST_TZ).shift(hours=15).isoformat(),
                get_next_weekday(0, TEST_TZ).shift(hours=16).isoformat(),
                None,
                False,
                None,
                None,
            ),
        ],
        expected_max_time_diff_days=1,
    )

    _test_create_event(
        request='Add my standup meeting to my work calendar for next Friday at 10-11 am. Note that we should discuss our feelings',
        expected_calls_any=[
            call.create_event(
                sentinel.ctx,
                'work_calendar_id',
                'Standup Meeting',
                get_next_weekday(4, TEST_TZ).shift(hours=10).isoformat(),
                get_next_weekday(4, TEST_TZ).shift(hours=11).isoformat(),
                None,
                False,
                None,
                'some notes',
            ),
        ],
        expected_max_time_diff_days=1,
    )

    _test_create_event(
        request='Schedule piano lessons every Thursday from 5:30-6pm starting next week',
        expected_calls_any=[
            call.create_event(
                sentinel.ctx,
                'primary_calendar_id',
                'Piano Lessons',
                get_next_weekday(3, TEST_TZ).shift(hours=17, minutes=30).isoformat(),
                get_next_weekday(3, TEST_TZ).shift(hours=18).isoformat(),
                None,
                False,
                [
                    'RRULE:FREQ=WEEKLY;BYDAY=TH',
                ],
                None,
            ),
        ],
        expected_max_time_diff_days=1,
    )
