from typing import Optional

import arrow
import yaml
from langchain.chat_models.openai import ChatOpenAI
from langchain.schema import HumanMessage
from llm_task_handler.handler import OpenAIFunctionTaskHandler
from llm_task_handler.handler import ProgressMessageFunc
from llm_task_handler.handler import TaskState

from secretary.calendar import get_calendar_service
from secretary.database import ChannelTable


class AnswerQuestionFromCalendar(OpenAIFunctionTaskHandler):
    def task_type(self) -> str:
        return 'answer_question_from_calendar'

    def intent_selection_function(self) -> dict:
        return {
            'name': self.task_type(),
            'description': f"Current time is {arrow.now().format('YYYY-MM-DDTHH:mm:ssZZ')}. Answer a question",
            'parameters': {
                'type': 'object',
                'properties': {
                    'question': {
                        'type': 'string',
                        'description': 'The question to answer',
                    },
                    'start_time': {
                        'type': 'string',
                        'description': 'Approximate start of time range that the question pertains to in the format YYYY-MM-DDTHH:mm:ssZZ. "this weekend" = the coming weekend.',
                    },
                    'end_time': {
                        'type': 'string',
                        'description': 'Approximate end of time range that the question pertains to in the format YYYY-MM-DDTHH:mm:ssZZ',
                    },
                    'is_question_about_past': {
                        'type': 'boolean',
                        'description': 'Whether the question pertains to events from the past',
                    },
                    'is_question_about_future': {
                        'type': 'boolean',
                        'description': 'Whether the question pertains to events in the future',
                    },
                },
                'required': ['question'],
            }
        }

    async def transition(
        self,
        cur_state: TaskState,
        progress_message_func: Optional[ProgressMessageFunc] = None,
    ) -> TaskState:
        args = cur_state.custom_state
        print(args)

        question = args['question']
        start_time, end_time = self._events_start_end_times(
            args.get('start_time'),
            args.get('end_time'),
            args.get('is_question_about_past'),
            args.get('is_question_about_future'),
        )

        print(f'Fetching events between {start_time} and {end_time}')

        # aiogoogle doesn't work for some reason
        google_apis_user_id = ChannelTable().look_up_user_id(self.user_id)
        events = get_calendar_service(google_apis_user_id).events().list(
            calendarId='primary',
            timeMin=start_time.isoformat() if start_time else None,
            timeMax=end_time.isoformat() if end_time else None,
            singleEvents=True,
            orderBy='startTime',
        ).execute().get('items', [])

        prompt = f'''
# Instructions

Current time is {arrow.now().format('YYYY-MM-DDTHH:mm:ssZZ')}.
Answer the question using only the provided events data.

# Question

{question}

# Events

'''

        prompt += self.events_yaml(events)

        chat_model = ChatOpenAI(  # type: ignore
            model_name='gpt-4-1106-preview',
            temperature=0,
            max_tokens=250,
        )

        reply = chat_model([
            HumanMessage(content=prompt),
        ])

        return TaskState(
            handler=self,
            user_prompt=prompt,
            reply=reply,
            is_done=True,
        )

    def events_yaml(self, events: list[dict]) -> str:
        return yaml.dump([
            {
                'when': self._get_time_phrase(event),
                'where': event.get('location'),
                'what': event.get('summary'),
                'details': event.get('description'),
            }
            for event in events
        ])

    def _events_start_end_times(
        self,
        q_start_time: Optional[str],
        q_end_time: Optional[str],
        is_question_about_past: Optional[bool],
        is_question_about_future: Optional[bool],
    ) -> tuple[arrow.Arrow, arrow.Arrow]:
        if q_start_time:
            start_time = arrow.get(q_start_time)

        if q_end_time:
            end_time = arrow.get(q_end_time)

        if is_question_about_past:
            if not q_start_time:
                start_time = arrow.now().shift(years=-1)
            if not q_end_time:
                end_time = arrow.now()

        if is_question_about_future:
            if not q_start_time:
                start_time = arrow.now()
            if not q_end_time:
                end_time = arrow.now().shift(years=1)

        return start_time, end_time

    def _get_time_phrase(self, event: dict) -> str:
        start = self._get_event_time(event['start']).to('US/Pacific')
        end = self._get_event_time(event['end']).to('US/Pacific')

        if 'dateTime' in event['start']:
            if start.date() == end.date():
                if start.hour == end.hour and start.minute == end.minute:
                    return f"on {start.format('YYYY-MM-DD')} at {start.format('h:mm a')}"
                else:
                    return f"on {start.format('YYYY-MM-DD')} from {start.format('h:mm a')} to {end.format('h:mm a')}"
            else:
                return f"from {start.naive} to {end.naive}"

        else:
            if start.date() == end.date():
                return f"on {start.format('YYYY-MM-DD')}"
            else:
                return f"from {start.format('YYYY-MM-DD')} to {end.format('YYYY-MM-DD')}"

    def _get_event_time(self, time_dict: dict) -> arrow.Arrow:
        if 'dateTime' in time_dict:
            return arrow.get(time_dict['dateTime'])
        else:
            return arrow.get(time_dict['date'])
