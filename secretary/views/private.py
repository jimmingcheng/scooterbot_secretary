import json

from agents import Runner
from django.http import HttpRequest
from django.http import HttpResponse

from secretary.agents.main_agent import SecretaryAgent


async def send_message_to_agent(request: HttpRequest) -> HttpResponse:
    payload = json.loads(request.body)
    user_id = payload["user_id"]
    message = payload["message"]

    user_ctx = SecretaryAgent.get_user_context(user_id)

    result = await Runner().run(
        SecretaryAgent(user_ctx),
        message,
        context=user_ctx,
    )

    return HttpResponse(result.final_output)
