import html
import json
from django.http import JsonResponse
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from urllib.parse import parse_qs
from urllib.parse import quote
from urllib.parse import unquote
from uuid import uuid1

from secretary.calendar import get_calendar_service
from secretary.clients import discord
from secretary.database import ChannelTable
from secretary.database import UserTable
from secretary.google_apis import get_userdb_client


def step2(request: HttpRequest) -> HttpResponse:
    user_id = request.GET.get('u', '')
    discord_channel = request.GET.get('ch', '')

    url = get_userdb_client().get_authorization_url(
        redirect_url='https://secretary.scooterbot.ai/login/step3',
        access_type='offline',
        state=f'u={user_id}&ch={discord_channel}',
        prompt='consent',
    )
    return HttpResponseRedirect(url)


def step3(request: HttpRequest) -> HttpResponse:
    code = request.GET['code']
    state = request.GET['state']

    google_apis_user_id = get_userdb_client().save_user_and_credentials(code)

    state_data = {k: v[0] for k, v in parse_qs(state).items()}
    user_id = state_data.get('u') or google_apis_user_id
    discord_channel = state_data.get('ch')

    url = (
        'https://secretary.scooterbot.ai/login/step4'
        f'?user_id={user_id}&google_apis_user_id={google_apis_user_id}'
    )
    if discord_channel:
        url += f'&discord_channel={discord_channel}'

    return HttpResponseRedirect(url)


def step4_calendar_list(request: HttpRequest) -> JsonResponse:
    google_apis_user_id = request.GET['google_apis_user_id']
    calendars = get_calendar_service(google_apis_user_id).calendarList().list().execute()['items']
    return JsonResponse({
        'calendars': [
            {
                'id': html.escape(cal['id']),
                'summary': html.escape(cal['summary']),
            }
            for cal in calendars
        ]
    })


def step5(request: HttpRequest) -> HttpResponse:
    discord_user_id = request.POST['user_id']
    google_apis_user_id = request.POST['google_apis_user_id']
    todo_calendar_id = request.POST['todo_calendar_id']
    discord_channel = request.POST['discord_channel']

    cal_service = get_calendar_service(google_apis_user_id)

    if todo_calendar_id == 'new':
        cal = cal_service.calendars().insert(
            body={
                'summary': '➤ To Do',
            }
        ).execute()
        todo_calendar_id = cal['id']

    ChannelTable().upsert(channel_user_id=discord_user_id, user_id=google_apis_user_id)
    UserTable().upsert(user_id=google_apis_user_id, todo_calendar_id=todo_calendar_id)

    cal = cal_service.calendars().get(calendarId=todo_calendar_id).execute()

    if discord_channel:
        discord.say(
            f"You're all set <@{discord_user_id}>. "
            f"I'll save your todos in this calendar: {cal['summary']}",
            channel=discord_channel
        )

    return HttpResponse(f"I'll save your todos in this calendar: {cal['summary']}")


def alexa_step1(request: HttpRequest) -> HttpResponse:
    alexa_state = request.GET['state']
    alexa_redirect_uri = request.GET['redirect_uri']

    state = _pack_alexa_state(alexa_state, alexa_redirect_uri)

    url = get_userdb_client().get_authorization_url(
        redirect_url='https://secretary.scooterbot.ai/login/alexa/step2',
        state=state,
        access_type='offline',
        prompt='consent',
    )

    return HttpResponseRedirect(url)


def alexa_step2(request: HttpRequest) -> HttpResponse:
    code = request.GET['code']
    state = request.GET['state']

    google_apis_user_id = get_userdb_client().save_user_and_credentials(code)

    url = _save_alexa_user_and_redirect(google_apis_user_id, state)

    return HttpResponseRedirect(url)


def _save_alexa_user_and_redirect(google_apis_user_id: str, state: str) -> str:
    alexa_state, alexa_redirect_uri = _unpack_alexa_state(state)
    alexa_access_token = str(uuid1())

    ChannelTable().upsert(channel_user_id=alexa_access_token, user_id=google_apis_user_id)
    UserTable().upsert(user_id=google_apis_user_id, todo_calendar_id='qrvfc4qvfm5d2kh0m6g9euo4s8@group.calendar.google.com')

    return (
        f'{alexa_redirect_uri}#state={alexa_state}'
        f'&token_type=Bearer&access_token={alexa_access_token}'
    )


def _pack_alexa_state(state: str, redirect_uri: str) -> str:
    return quote(json.dumps(
        {'state': state, 'redirect_uri': redirect_uri}
    ))


def _unpack_alexa_state(state: str) -> tuple:
    unpacked = json.loads(unquote(state))
    return unpacked['state'], unpacked['redirect_uri']
