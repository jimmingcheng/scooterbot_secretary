from typing import Any
from typing import Iterator

import pytest
from contextlib import contextmanager
from unittest.mock import patch
from agents._run_impl import NextStepHandoff

from agents import Agent as OpenAIAgent


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
    import secretary
    secretary.init('tests/secretary.yaml')
