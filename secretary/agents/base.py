import textwrap
from dataclasses import dataclass

from agents import Agent as OpenAIAgent
from agents import RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from secretary.account_linking import get_account_link_manager


@dataclass
class UserContext:
    user_id: str
    tesla_user_id: str | None = None
    house_user_id: str | None = None


UserContextWrapper = RunContextWrapper[UserContext]


class BaseSecretaryAgent(OpenAIAgent):
    @classmethod
    def get_user_context(cls, user_id: str) -> UserContext:
        tesla_user_id = get_account_link_manager().get_linked_user_id(user_id, 'tesla')
        house_user_id = get_account_link_manager().get_linked_user_id(user_id, 'house')

        return UserContext(
            user_id=user_id,
            tesla_user_id=tesla_user_id,
            house_user_id=house_user_id,
        )

    def agent_app_context(self):
        return textwrap.dedent(
            f'''\
            {RECOMMENDED_PROMPT_PREFIX}

            # Application Context

            Scooterbot AI's Secretary Agent is a virtual personal assistant with access to various
            tools linked to the user's personal data and assets.

            '''
        )
