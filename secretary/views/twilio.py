import asyncio
from django.http import HttpRequest
from django.http import HttpResponse
from llm_task_handler.dispatch import TaskDispatcher
from twilio.twiml.messaging_response import MessagingResponse

from secretary.database import ChannelTable
from secretary.tasks.calendar import AddCalendarEventFromSMS
from secretary.tasks.question import AnswerQuestionFromCalendar
from secretary.tasks.todo import AddTodoFromSMS


def sms_reply(request: HttpRequest) -> HttpResponse:
    sms_number = request.POST.get('From')
    user_prompt = request.POST.get('Body')

    user_id = ChannelTable().look_up_user_id('sms', sms_number)
    reply = asyncio.run(
        TaskDispatcher([
            AnswerQuestionFromCalendar(user_id=user_id),
            AddCalendarEventFromSMS(user_id=user_id),
            AddTodoFromSMS(user_id=user_id),
        ]).reply(user_prompt)
    )

    response = MessagingResponse()
    response.message(reply)

    return HttpResponse(str(response))
