from typing import Any
from typing import Iterator

import arrow
import pytest
from contextlib import contextmanager
from unittest.mock import patch
from agents import Agent as OpenAIAgent
from agents import set_tracing_disabled
from agents._run_impl import NextStepHandoff


class NoopAgent(OpenAIAgent):
    def __init__(self) -> None:
        super().__init__(
            name=self.__class__.__name__,
            model='gpt-4o-mini',
            output_type=str,
            instructions='Simply reply with "ok"',
        )


@contextmanager
def capture_handoffs() -> Iterator[list[type[OpenAIAgent]]]:
    handoffs = []
    orig_ctor = NextStepHandoff

    def side_effect(new_agent: OpenAIAgent) -> NextStepHandoff:
        handoffs.append(type(new_agent))
        return orig_ctor(NoopAgent())

    with patch('agents._run_impl.NextStepHandoff', side_effect=side_effect):
        yield handoffs


class ToolCallTracker:
    _tool_calls: list[Any] = []

    def reset(self) -> None:
        self._tool_calls = []

    def add(self, tool_call: Any) -> None:
        self._tool_calls += [tool_call]

    def get(self) -> list[Any]:
        return self._tool_calls


@pytest.fixture(autouse=True)
def run_secretary_init() -> None:
    set_tracing_disabled(True)
    import secretary
    secretary.init('tests/secretary.yaml')


def get_next_weekday(day_index: int, tz='local') -> arrow.Arrow:
    """
    monday=0
    """
    now = arrow.now(tz)
    days_ahead = (day_index - now.weekday() + 7) % 7 or 7
    next_day = now.shift(days=days_ahead).replace(hour=0, minute=0, second=0, microsecond=0)
    return next_day
