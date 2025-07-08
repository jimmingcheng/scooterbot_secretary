from typing import Optional

import html
import json
from dataclasses import dataclass
from django.http import JsonResponse
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from oauth_userdb.client import OAuthUserDBClient
from urllib.parse import quote
from urllib.parse import unquote
from uuid import uuid1

from secretary.calendar import get_calendar_service
from secretary.data_models import SecretaryChannel
from secretary.data_models import User
from secretary.google_apis import get_oauth_client
from secretary.notifications import notify


def oauth_client() -> OAuthUserDBClient:
    return get_oauth_client(
        redirect_url='https://secretary.scooterbot.ai/login/step3',
    )


def alexa_oauth_client() -> OAuthUserDBClient:
    return get_oauth_client(
        redirect_url='https://secretary.scooterbot.ai/login/alexa/step2',
    )


@dataclass
class OAuthState:
    discord_user_id: Optional[str]

    def pack(self) -> str:
        return quote(json.dumps({
            'discord_user_id': self.discord_user_id,
        }))

    @classmethod
    def unpack(cls, state: str) -> 'OAuthState':
        unpacked = json.loads(unquote(state))
        return OAuthState(
            discord_user_id=unpacked['discord_user_id'],
        )


def step2(request: HttpRequest) -> HttpResponse:
    discord_user_id = request.GET.get('discord_user_id')

    url = oauth_client().get_authorization_url(
        access_type='offline',
        state=OAuthState(discord_user_id=discord_user_id).pack(),
        prompt='consent',
    )
    return HttpResponseRedirect(url)


def step3(request: HttpRequest) -> HttpResponse:
    code = request.GET['code']
    state = OAuthState.unpack(request.GET['state'])

    user_id = oauth_client().save_user_and_credentials(code)

    url = f'https://secretary.scooterbot.ai/login/step4?user_id={user_id}'
    if state.discord_user_id:
        url += f'&discord_user_id={state.discord_user_id}'

    return HttpResponseRedirect(url)


def step4_calendar_list(request: HttpRequest) -> JsonResponse:
    user_id = request.GET['user_id']
    calendars = get_calendar_service(user_id).calendarList().list().execute()['items']
    return JsonResponse({
        'calendars': [
            {
                'id': html.escape(cal['id']),
                'summary': html.escape(cal['summary']),
            }
            for cal in calendars
        ]
    })


async def step5(request: HttpRequest) -> HttpResponse:
    user_id = request.POST['user_id']
    todo_calendar_id = request.POST['todo_calendar_id']
    discord_user_id = request.POST['discord_user_id']
    sms_number = request.POST['sms_number']

    cal_service = get_calendar_service(user_id)

    if todo_calendar_id == 'new':
        cal = cal_service.calendars().insert(
            body={
                'summary': '➤ To Do',
            }
        ).execute()
        todo_calendar_id = cal['id']

    if discord_user_id:
        SecretaryChannel.upsert(
            SecretaryChannel(
                channel_type='discord',
                channel_user_id=discord_user_id,
                user_id=user_id,
                push_enabled=True,
            )
        )
    if sms_number:
        SecretaryChannel.upsert(
            SecretaryChannel(
                channel_type='sms',
                channel_user_id=sms_number,
                user_id=user_id,
                push_enabled=True,
            )
        )

    User.upsert(User(user_id=user_id))

    cal = cal_service.calendars().get(calendarId=todo_calendar_id).execute()

    await notify(user_id, "You're all set! I'll save your todos in this calendar: " + cal['summary'])

    return HttpResponse("You're all set! I'll save your todos in this calendar: " + cal['summary'])


def alexa_step1(request: HttpRequest) -> HttpResponse:
    alexa_state = request.GET['state']
    alexa_redirect_uri = request.GET['redirect_uri']

    state = _pack_alexa_state(alexa_state, alexa_redirect_uri)

    url = alexa_oauth_client().get_authorization_url(
        state=state,
        access_type='offline',
        prompt='consent',
    )

    return HttpResponseRedirect(url)


def alexa_step2(request: HttpRequest) -> HttpResponse:
    code = request.GET['code']
    state = request.GET['state']

    user_id = alexa_oauth_client().save_user_and_credentials(code)

    url = _save_alexa_user_and_redirect(user_id, state)

    return HttpResponseRedirect(url)


def _save_alexa_user_and_redirect(user_id: str, state: str) -> str:
    alexa_state, alexa_redirect_uri = _unpack_alexa_state(state)
    alexa_access_token = str(uuid1())

    channel = SecretaryChannel(
        channel_type='alexa',
        channel_user_id=alexa_access_token,
        user_id=user_id,
        push_enabled=False,
    )

    SecretaryChannel.upsert(channel)
    User.upsert(User(user_id=user_id))

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
