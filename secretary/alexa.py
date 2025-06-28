import asyncio
import logging

from agents import Runner
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

from secretary.agents.base import UserContext
from secretary.agents.main_agent import SecretaryAgent
from secretary.database import Channel
from secretary.database import ChannelTable


class IssuePromptHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name('IssuePrompt')(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        access_token = str(handler_input.request_envelope.context.system.user.access_token)  # type: ignore
        intent = handler_input.request_envelope.request.intent  # type: ignore
        user_prompt = intent.slots['Prompt'].value  # type: ignore

        user = ChannelTable.get(Channel.make_channel_id('alexa', access_token))

        result = asyncio.run(
            Runner().run(
                SecretaryAgent(user.user_id),
                f"{user_prompt} (reply in natural spoken language)",
                context=UserContext(user_id=user.user_id),
            )
        )

        reply = result.final_output

        handler_input.response_builder.speak(reply).set_should_end_session(True)
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
