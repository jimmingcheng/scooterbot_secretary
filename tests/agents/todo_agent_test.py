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
from secretary.agents.todo_agent import TodoAgent
from secretary.agents.todo_agent import TodosResult
from tests.conftest import ToolCallTracker, get_next_weekday


TOOL_CALLS = ToolCallTracker()
TEST_TZ = 'America/New_York'
NOW = arrow.now(TEST_TZ)


@function_tool
async def list_todos(
    ctx: UserContextWrapper,
    due_date_min: str,
    due_date_max: str,
) -> TodosResult:
    TOOL_CALLS.add(
        call.list_todos(
            sentinel.ctx,
            due_date_min,
            due_date_max,
        )
    )
    return TodosResult(todos=[], error_message=None)


@function_tool
async def create_todo(
    ctx: UserContextWrapper,
    summary: str,
    due_date: str,
    location: str | None,
    rfc5545_recurrence_properties: list[str] | None,
    notes: str | None,
) -> str:
    TOOL_CALLS.add(
        call.create_todo(
            sentinel.ctx,
            summary,
            due_date,
            location,
            rfc5545_recurrence_properties,
            notes,
        )
    )
    return 'Successfully created todo'


@pytest.fixture(autouse=True)
def mock_all_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr('secretary.agents.todo_agent.list_todos', list_todos)
    monkeypatch.setattr('secretary.agents.todo_agent.create_todo', create_todo)


@pytest.fixture(autouse=True)
def mock_calendar_service() -> None:
    with patch('secretary.agents.todo_agent.get_calendar_service') as mock_func:
        mock_func.return_value.settings.return_value.get.return_value.execute.return_value = {
            'value': TEST_TZ,
        }
        yield mock_func


def run_agent(request: str) -> str:
    ctx = UserContext(user_id='test_user_id')

    result = asyncio.run(
        Runner().run(
            TodoAgent(ctx),
            request,
            context=ctx,
        )
    )

    return result.final_output


def _test_list_todos(
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
        _, actual_min, actual_max = actual.args
        _, expected_min, expected_max = expected.args

        if abs((arrow.get(actual_min) - arrow.get(expected_min)).days) > expected_max_time_diff_days:
            return False
        if abs((arrow.get(actual_max) - arrow.get(expected_max)).days) > expected_max_time_diff_days:
            return False
        return True

    assert any(
        is_similar(actual, expected) for actual, expected in test_pairs
    ), f'Actual calls {actual_calls} did not match expected calls {expected_calls_any}'


def test_list_upcoming_todos() -> None:
    _test_list_todos(
        request="What are my upcoming todos?",
        expected_calls_any=[
            call.list_todos(
                sentinel.ctx,
                NOW.format('YYYY-MM-DD'),
                NOW.shift(months=6).format('YYYY-MM-DD'),
            ),
        ],
        expected_max_time_diff_days=2,
    )


def test_list_past_todos() -> None:
    _test_list_todos(
        request="What were my todos from the last 6 months?",
        expected_calls_any=[
            call.list_todos(
                sentinel.ctx,
                NOW.shift(months=-6).format('YYYY-MM-DD'),
                NOW.format('YYYY-MM-DD'),
            ),
        ],
        expected_max_time_diff_days=2,
    )


def test_list_all_todos() -> None:
    _test_list_todos(
        request="Show me all my todos",
        expected_calls_any=[
            call.list_todos(
                sentinel.ctx,
                NOW.shift(months=-6).format('YYYY-MM-DD'),
                NOW.shift(months=6).format('YYYY-MM-DD'),
            ),
        ],
        expected_max_time_diff_days=2,
    )


def _test_create_todo(
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
            actual_summary,
            actual_due,
            actual_location,
            actual_rfc,
            actual_notes,
        ) = actual.args
        (
            _,
            expected_summary,
            expected_due,
            expected_location,
            expected_rfc,
            expected_notes,
        ) = expected.args

        if abs((arrow.get(actual_due) - arrow.get(expected_due)).days) > expected_max_time_diff_days:
            return False
        if bool(actual_location) != bool(expected_location):
            return False
        if actual_rfc != expected_rfc:
            return False
        if bool(actual_notes) != bool(expected_notes):
            return False
        return True

    assert any(
        is_similar(actual, expected) for actual, expected in test_pairs
    ), f'Actual calls {actual_calls} did not match expected calls {expected_calls_any}'


def test_create_simple_todo() -> None:
    due = get_next_weekday(0, TEST_TZ).format('YYYY-MM-DD')
    _test_create_todo(
        request='Add a todo to walk the dog next Monday',
        expected_calls_any=[
            call.create_todo(
                sentinel.ctx,
                'Walk the Dog',
                due,
                None,
                None,
                None,
            ),
        ],
        expected_max_time_diff_days=1,
    )


def test_create_todo_with_notes_and_location() -> None:
    due = get_next_weekday(5, TEST_TZ).format('YYYY-MM-DD')
    _test_create_todo(
        request='Add a todo to buy groceries next Saturday at the supermarket. Note remember to buy eggs',
        expected_calls_any=[
            call.create_todo(
                sentinel.ctx,
                'Buy Groceries',
                due,
                'the supermarket',
                None,
                'remember to buy eggs',
            ),
        ],
        expected_max_time_diff_days=1,
    )
