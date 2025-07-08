from __future__ import annotations

import json
from dataclasses import dataclass
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from oauth_userdb.client import OAuthUserDBClient
from urllib.parse import quote
from urllib.parse import unquote

from secretary.data_models import SecretaryChannel
from secretary.data_models import User
from secretary.google_apis import get_oauth_client
from secretary.notifications import notify


def oauth_client() -> OAuthUserDBClient:
    return get_oauth_client(
        redirect_url='https://secretary.scooterbot.ai/setup/step2',
    )


@dataclass
class OAuthState:
    discord_user_id: str | None = None
    sms_number: str | None = None

    def pack(self) -> str:
        return quote(json.dumps({
            'discord_user_id': self.discord_user_id,
            'sms_number': self.sms_number,
        }))

    @classmethod
    def unpack(cls, state: str) -> OAuthState:
        unpacked = json.loads(unquote(state))
        return OAuthState(
            discord_user_id=unpacked['discord_user_id'],
            sms_number=unpacked['sms_number'],
        )


def step1(request: HttpRequest) -> HttpResponse:
    discord_user_id = request.GET.get('du')
    sms_number = request.GET.get('sms')

    url = oauth_client().get_authorization_url(
        access_type='offline',
        state=OAuthState(
            discord_user_id=discord_user_id,
            sms_number=sms_number,
        ).pack(),
        prompt='consent',
    )
    return HttpResponseRedirect(url)


async def step2(request: HttpRequest) -> HttpResponse:
    code = request.GET['code']
    state = OAuthState.unpack(request.GET['state'])

    user_id = oauth_client().save_user_and_credentials(code)

    User.upsert(User(user_id=user_id))

    if state.discord_user_id:
        SecretaryChannel.upsert(
            SecretaryChannel(
                channel_type='discord',
                channel_user_id=state.discord_user_id,
                user_id=user_id,
                push_enabled=True,
            )
        )
    if state.sms_number:
        SecretaryChannel.upsert(
            SecretaryChannel(
                channel_type='sms',
                channel_user_id=state.sms_number,
                user_id=user_id,
                push_enabled=True,
            )
        )

    await notify(user_id, "You're all set!")

    return HttpResponse("You're all set!")
