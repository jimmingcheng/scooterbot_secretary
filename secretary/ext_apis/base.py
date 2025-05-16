from abc import ABC
from abc import abstractmethod
import json
import textwrap
from openai import OpenAI


class ExternalAPI(ABC):
    @abstractmethod
    def overview(cls) -> str:
        """Succinct description of what this API does. To be read by LLM to decide whether to use
        this API."""

    @abstractmethod
    def usage_guide(self) -> str:
        """Detailed description of the API's capabilities and how to invoke them. Should instruct
        the LLM to call the `invoke_api` tool
        """

    @abstractmethod
    def invoke_api(self, **args) -> str:
        """Implements the `invoke_api` tool."""

    @abstractmethod
    def tool_spec_for_invoke_api(self) -> dict:
        """OpenAI tool spec for the `invoke_api` tool."""

    def initial_data(self) -> str:
        return ''

    def answer(
        self,
        query: str,
        data_from_last_step: str | None = None,
        depth: int = 0,
        max_depth: int = 3
    ) -> str:
        if not data_from_last_step:
            data_from_last_step = self.initial_data()

        system_prompt = textwrap.dedent(
            '''\
            # Instructions

            You are given `query` and `data_from_last_step`.

            1. If `data_from_last_step` is sufficient to answer query, create and return `answer` (plain English)
            2. Else, call `invoke_api` to fetch more data, so the process can be repeated with the additional data

            # API Usage Guide

            {usage_guide}
            '''
        ).format(
            usage_guide=self.usage_guide()
        )
        print(self.usage_guide())

        user_prompt = textwrap.dedent(
            '''\
            # Query

            {query}

            # Data from last step

            {data_from_last_step}
            '''
        ).format(
            query=query,
            data_from_last_step=data_from_last_step,
        )

        completion_message = OpenAI().chat.completions.create(
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            model='gpt-4o',
            tools=[
                self.tool_spec_for_invoke_api(),  # type: ignore
                {
                    "type": "function",
                    "function": {
                        "name": "answer",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "answer": {"type": "string"},
                            },
                            "required": ["answer"],
                        }
                    }
                }
            ],
            tool_choice='required',
        ).choices[0].message

        print(completion_message)
        print(data_from_last_step)

        if completion_message.tool_calls:
            assert completion_message.tool_calls

            tool_call = completion_message.tool_calls[0]

            func_args = json.loads(tool_call.function.arguments)
            if tool_call.function.name == 'invoke_api':
                data_from_last_step += '\n\n---\n\n' + self.invoke_api(**func_args)
                if depth < max_depth:
                    return self.answer(query, data_from_last_step, depth + 1, max_depth)
                else:
                    return data_from_last_step
            elif tool_call.function.name == 'answer':
                return func_args['answer']
            raise ValueError('Unexpected tool call')
        else:
            assert completion_message.content
            return completion_message.content
