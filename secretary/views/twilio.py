import asyncio
from django.http import HttpRequest
from django.http import HttpResponse
from llm_task_handler.dispatch import TaskDispatcher
from twilio.twiml.messaging_response import MessagingResponse

from secretary.data_models import SecretaryChannel
from secretary.tasks.question import AnswerQuestionFromCalendar
from secretary.tasks.todo import AddTodoFromSMS


def sms_reply(request: HttpRequest) -> HttpResponse:
    sms_number = request.POST.get('From')
    user_prompt = request.POST.get('Body')

    user = SecretaryChannel.get(SecretaryChannel.make_channel_id('sms', sms_number))
    reply = asyncio.run(
        TaskDispatcher([
            AnswerQuestionFromCalendar(user_id=user.user_id),
            AddTodoFromSMS(user_id=user.user_id),
        ]).reply(user_prompt)
    )

    response = MessagingResponse()
    response.message(reply)

    return HttpResponse(str(response))
