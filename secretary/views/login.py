from typing import Optional

import html
import json
from dataclasses import dataclass
from django.http import JsonResponse
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from urllib.parse import quote
from urllib.parse import unquote
from uuid import uuid1

from secretary.calendar import get_calendar_service
from secretary.clients import discord
from secretary.database import ChannelTable
from secretary.database import UserTable
from secretary.google_apis import get_userdb_client


@dataclass
class OAuthState:
    discord_user_id: Optional[str]
    discord_channel: Optional[str]

    def pack(self) -> str:
        return quote(json.dumps({
            'discord_user_id': self.discord_user_id,
            'discord_channel': self.discord_channel,
        }))

    @classmethod
    def unpack(cls, state: str) -> 'OAuthState':
        unpacked = json.loads(unquote(state))
        return OAuthState(
            discord_user_id=unpacked['discord_user_id'],
            discord_channel=unpacked['discord_channel'],
        )


def step2(request: HttpRequest) -> HttpResponse:
    discord_user_id = request.GET.get('discord_user_id')
    discord_channel = request.GET.get('discord_channel')

    url = get_userdb_client().get_authorization_url(
        redirect_url='https://secretary.scooterbot.ai/login/step3',
        access_type='offline',
        state=OAuthState(discord_user_id=discord_user_id, discord_channel=discord_channel).pack(),
        prompt='consent',
    )
    return HttpResponseRedirect(url)


def step3(request: HttpRequest) -> HttpResponse:
    code = request.GET['code']
    state = OAuthState.unpack(request.GET['state'])

    user_id = get_userdb_client().save_user_and_credentials(code)

    url = f'https://secretary.scooterbot.ai/login/step4?user_id={user_id}'
    if state.discord_user_id:
        url += f'&discord_user_id={state.discord_user_id}'
    if state.discord_channel:
        url += f'&discord_channel={state.discord_channel}'

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


def step5(request: HttpRequest) -> HttpResponse:
    user_id = request.POST['user_id']
    todo_calendar_id = request.POST['todo_calendar_id']
    discord_user_id = request.POST['discord_user_id']
    discord_channel = request.POST['discord_channel']
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
        ChannelTable().upsert(channel_type='discord', channel_user_id=discord_user_id, user_id=user_id)
    if sms_number:
        ChannelTable().upsert(channel_type='sms', channel_user_id=sms_number, user_id=user_id)

    UserTable().upsert(user_id=user_id, todo_calendar_id=todo_calendar_id)

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

    user_id = get_userdb_client().save_user_and_credentials(code)

    url = _save_alexa_user_and_redirect(user_id, state)

    return HttpResponseRedirect(url)


def _save_alexa_user_and_redirect(user_id: str, state: str) -> str:
    alexa_state, alexa_redirect_uri = _unpack_alexa_state(state)
    alexa_access_token = str(uuid1())

    ChannelTable().upsert(channel_type='alexa', channel_user_id=alexa_access_token, user_id=user_id)
    UserTable().upsert(user_id=user_id, todo_calendar_id='qrvfc4qvfm5d2kh0m6g9euo4s8@group.calendar.google.com')

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
