import arrow
from django.http import HttpRequest
from django.http import JsonResponse

from secretary import read


def get_todos_for_day(request: HttpRequest) -> JsonResponse:
    user_id = request.GET['user_id']
    dt = request.GET.get('dt')

    dt = arrow.get(dt) if dt else None

    todos = read.get_todos_for_day(user_id, dt)

    return JsonResponse({'todos': todos})
