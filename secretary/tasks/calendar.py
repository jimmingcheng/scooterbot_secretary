from typing import Optional

import arrow
from abc import ABC
from abc import abstractmethod
from llm_task_handler.handler import OpenAIFunctionTaskHandler
from llm_task_handler.handler import ProgressMessageFunc
from llm_task_handler.handler import TaskState

from secretary import celery_tasks


class AddCalendarEventBase(OpenAIFunctionTaskHandler, ABC):
    def task_type(self) -> str:
        return 'add_calendar_event'

    @abstractmethod
    def confirmation_message_description(self) -> str:
        pass

    def intent_selection_function(self) -> dict:
        return {
            'name': 'add_calendar_event',
            'description': f"Current time is {arrow.now().format('YYYY-MM-DDTHH:mm:ssZZ')}. Prepare to add a calendar event",
            'parameters': {
                'type': 'object',
                'properties': {
                    'title': {
                        'type': 'string',
                    },
                    'start_time': {
                        'type': 'string',
                        'description': 'Start time in the format YYYY-MM-DDTHH:mm:ssZZ. "this weekend" = the coming weekend.',
                    },
                    'end_time': {
                        'type': 'string',
                        'description': 'End time in the format YYYY-MM-DDTHH:mm:ssZZ',
                    },
                    'is_all_day': {
                        'type': 'boolean',
                        'description': 'Whether it is an all day event',
                    },
                    'location': {
                        'type': 'string',
                        'description': 'Location of the event',
                    },
                    'confirmation_message': {
                        'type': 'string',
                        'description': self.confirmation_message_description(),
                    },
                },
                'required': ['title', 'start_time', 'end_time', 'is_all_day', 'confirmation_message'],
            }
        }

    async def transition(
        self,
        cur_state: TaskState,
        progress_message_func: Optional[ProgressMessageFunc] = None,
    ) -> TaskState:
        if cur_state.state_id == self.INTENT_SELECTION_STATE_ID:
            return TaskState(
                handler=self,
                user_prompt=cur_state.user_prompt,
                custom_state=cur_state.custom_state,
            )

        else:
            celery_tasks.add_calendar_event.delay(self.user_id, cur_state.custom_state)

            return TaskState(
                handler=self,
                user_prompt=cur_state.user_prompt,
                reply=cur_state.custom_state['confirmation_message'],
                is_done=True,
            )


class AddCalendarEventFromSMS(AddCalendarEventBase):
    def confirmation_message_description(self) -> str:
        return """
SMS message to be sent to the user. e.g.:

Added to your calendar:

Title: Doctor's appointment
Date/Time: October 5, 2023, 4-6:30pm
Location: 123 Main St, San Francisco, CA 94105
        """


class AddCalendarEventFromAlexa(AddCalendarEventBase):
    def confirmation_message_description(self) -> str:
        return """
Speech to be read to the user via Alexa. e.g.:

I've added your doctor's appointment to your calendar on October 5 from 4 to 6:30pm at 123 Main Street in San Francisco.
        """


class AddCalendarEventFromDiscord(AddCalendarEventBase):
    def confirmation_message_description(self) -> str:
        return """
Human-readable confirmation of the fields that the event has been added with. e.g.:

Added to your calendar:

>>> Title: **Doctor's appointment**
Date/Time: **October 5, 2023, 4-6:30pm**
Location: **123 Main St, San Francisco, CA 94105**
        """
