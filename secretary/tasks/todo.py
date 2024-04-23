from typing import Optional

import arrow
from abc import ABC
from abc import abstractmethod
from llm_task_handler.handler import OpenAIFunctionTaskHandler
from llm_task_handler.handler import ProgressMessageFunc
from llm_task_handler.handler import TaskState

from secretary.write import add_todo
from secretary.read import get_todos
from secretary.read import Todo


class GetTodosBase(OpenAIFunctionTaskHandler, ABC):
    def task_type(self) -> str:
        return 'list_todos_reminders_or_tasks'

    @abstractmethod
    def formatted_reply(self, todos: list[Todo]) -> str:
        pass

    def intent_selection_function(self) -> dict:
        return {
            'name': self.task_type(),
            'description': 'List todos, reminders, or tasks.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'start_date': {
                        'type': 'string',
                        'description': 'Approximate start of date range to fetch from in the format YYYY-MM-DD. "this weekend" = the coming weekend. If not provided, defaults to today.',
                    },
                    'end_date': {
                        'type': 'string',
                        'description': 'Approximate end of date range to fetch from in the format YYYY-MM-DD. "this weekend" = the coming weekend. If not provided, defaults to 7 days from now.',
                    },
                },
                'required': ['task_name', 'start_date', 'end_date'],
            }
        }

    async def transition(
        self,
        cur_state: TaskState,
        progress_message_func: Optional[ProgressMessageFunc] = None,
    ) -> TaskState:
        cs = cur_state.custom_state

        todos = get_todos(
            self.user_id,
            arrow.get(cs['start_date']),
            arrow.get(cs['end_date']),
        )

        reply = self.formatted_reply(todos)

        return TaskState(
            handler=self,
            user_prompt=cur_state.user_prompt,
            reply=reply,
            is_done=True,
        )


class GetTodosFromSMS(GetTodosBase):
    def formatted_reply(self, todos: list[Todo]) -> str:
        return '\n\n'.join([
            (
                f'{todo.task_name}\n'
                f"(due {todo.due_date.format('dddd, MMMM D, YYYY')})"
            )
            for todo in todos
        ])


class GetTodosFromDiscord(GetTodosBase):
    def formatted_reply(self, todos: list[Todo]) -> str:
        return '>>> ' + '\n\n'.join([
            (
                f'**{todo.task_name}**\n'
                f'{todo.due_date.format("dddd, MMMM D, YYYY")}'
            )
            for todo in todos
        ])


class AddTodoBase(OpenAIFunctionTaskHandler, ABC):
    def task_type(self) -> str:
        return 'add_todo_reminder_or_task'

    @abstractmethod
    def formatted_reply(self, task_name: str, due_date: arrow.Arrow) -> str:
        pass

    def intent_selection_function(self) -> dict:
        return {
            'name': self.task_type(),
            'description': 'Add a todo, reminder, or task. If there are multiple separate requests, process the most recent one.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'task_name': {
                        'type': 'string',
                    },
                    'due_date': {
                        'type': 'string',
                        'description': f'Current date is {arrow.now().format("YYYY-MM-DD")}',
                    },
                },
                'required': ['task_name'],
            }
        }

    async def transition(
        self,
        cur_state: TaskState,
        progress_message_func: Optional[ProgressMessageFunc] = None,
    ) -> TaskState:
        cs = cur_state.custom_state

        due_date = arrow.get(cs['due_date']) if 'due_date' in cs else arrow.now()

        add_todo(self.user_id, cs['task_name'], due_date)

        reply = self.formatted_reply(cs['task_name'], due_date)

        return TaskState(
            handler=self,
            user_prompt=cur_state.user_prompt,
            reply=reply,
            is_done=True,
        )


class AddTodoFromSMS(AddTodoBase):
    def formatted_reply(self, task_name: str, due_date: arrow.Arrow) -> str:
        return f'''
Here's your todo:

Todo: {task_name}
Due: {due_date.format('dddd, MMMM D, YYYY')}
'''


class AddTodoFromAlexa(AddTodoBase):
    def formatted_reply(self, task_name: str, due_date: arrow.Arrow) -> str:
        return f'''
I'll remind you to {task_name} on {due_date.format('dddd')},
<say-as interpret-as="date">{due_date.format('YYYY-MM-DD')}</say-as>.
'''


class AddTodoFromDiscord(AddTodoBase):
    def formatted_reply(self, task_name: str, due_date: arrow.Arrow) -> str:
        return f'''
Here's your todo:
>>> **{task_name}**
{due_date.format('dddd, MMMM D, YYYY')}
'''
