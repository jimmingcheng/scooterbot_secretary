import asyncio
import sys
from llm_task_handler.dispatch import TaskDispatcher

import secretary
from secretary.tasks.question import AnswerQuestionFromCalendar


def reply(user_prompt: str):
    user_id = '804756148007862332'
    return asyncio.run(
        TaskDispatcher([
            AnswerQuestionFromCalendar(user_id=user_id),
        ]).reply(user_prompt)
    )


if __name__ == '__main__':
    secretary.init()
    print(reply(sys.argv[1]))
