import arrow
import re
import json
import staticconf
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseForbidden


from secretary import write


def _get_token() -> str:
    return staticconf.read('webhook_token', namespace='secretary')  # type: ignore


def _is_authorized(request: HttpRequest) -> bool:
    m = re.match(r'^Bearer (.*)$', request.headers['Authorization'])

    if not m:
        return False
    elif m[1] == _get_token():
        return True
    else:
        return False


def add_todo(request: HttpRequest) -> HttpResponse:
    if not _is_authorized(request):
        return HttpResponseForbidden()

    todo_request = json.loads(request.body.decode('utf-8'))

    date = todo_request.get('date')
    date = arrow.get(date) if date else None

    todo, reminder_days_before = write.add_todo(
        todo_request['user_id'],
        todo_request['title'],
        date,
    )

    response_speech = todo_request['confirmation_message']

    if reminder_days_before > 0:
        todo_start_time = write.event_start_time(todo)

        duration = todo_start_time.humanize(
            other=todo_start_time.shift(days=-reminder_days_before),
            only_distance=True
        )
        response_speech += f" I'll remind you {duration} before."

    return HttpResponse(response_speech)
