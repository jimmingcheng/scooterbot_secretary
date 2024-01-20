import asyncio
import logging
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_model.intent import Intent
from ask_sdk_model.slot import Slot
from ask_sdk_model.dialog.delegate_directive import DelegateDirective
from ask_sdk_runtime.exceptions import DispatchException
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_intent_name
from ask_sdk_core.utils import is_request_type
from llm_task_handler.dispatch import TaskDispatcher

from secretary.database import ChannelTable
from secretary.tasks.calendar import AddCalendarEventFromAlexa
from secretary.tasks.question import AnswerQuestionFromCalendar
from secretary.tasks.todo import AddTodoFromAlexa


class IssuePromptHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name('IssuePrompt')(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        access_token = str(handler_input.request_envelope.context.system.user.access_token)  # type: ignore
        intent = handler_input.request_envelope.request.intent  # type: ignore
        user_prompt = intent.slots['Prompt'].value  # type: ignore

        user_id = ChannelTable().look_up_user_id('alexa', access_token)
        speech = asyncio.run(
            TaskDispatcher([
                AnswerQuestionFromCalendar(user_id=user_id),
                AddCalendarEventFromAlexa(user_id=user_id),
                AddTodoFromAlexa(user_id=user_id),
            ]).reply(user_prompt)
        )

        handler_input.response_builder.speak(speech).set_should_end_session(True)
        return handler_input.response_builder.response


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type('LaunchRequest')(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        updated_intent = Intent(
            name='IssuePrompt',
            slots={
                'Prompt': Slot(name='Prompt', value=None),
            }
        )
        handler_input.response_builder.add_directive(DelegateDirective(updated_intent))
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return False

    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        if not isinstance(exception, DispatchException):
            logging.exception('Exception while responding to Alexa request')

        handler_input.response_builder.speak('Sorry, something went wrong.').set_should_end_session(True)
        return handler_input.response_builder.response


def get_skill_builder() -> SkillBuilder:
    sb = CustomSkillBuilder(api_client=DefaultApiClient())
    sb.add_request_handler(IssuePromptHandler())
    sb.add_request_handler(LaunchRequestHandler())
    sb.add_exception_handler(CatchAllExceptionHandler())
    return sb
