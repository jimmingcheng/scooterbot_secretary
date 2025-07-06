import json
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from oauth_userdb.client import OAuthUserDBClient
from urllib.parse import quote
from urllib.parse import unquote
from uuid import uuid1

from secretary.database import Channel
from secretary.database import ChannelTable
from secretary.database import User
from secretary.database import UserTable
from secretary.google_apis import get_oauth_client


def oauth_client() -> OAuthUserDBClient:
    return get_oauth_client(
        redirect_url='https://secretary.scooterbot.ai/setup/alexa/step2',
    )


def step1(request: HttpRequest) -> HttpResponse:
    alexa_state = request.GET['state']
    alexa_redirect_uri = request.GET['redirect_uri']

    state = _pack_alexa_state(alexa_state, alexa_redirect_uri)

    url = oauth_client().get_authorization_url(
        state=state,
        access_type='offline',
        prompt='consent',
    )

    return HttpResponseRedirect(url)


def step2(request: HttpRequest) -> HttpResponse:
    code = request.GET['code']
    state = request.GET['state']

    user_id = oauth_client().save_user_and_credentials(code)

    url = _save_alexa_user_and_redirect(user_id, state)

    return HttpResponseRedirect(url)


def _save_alexa_user_and_redirect(user_id: str, state: str) -> str:
    alexa_state, alexa_redirect_uri = _unpack_alexa_state(state)
    alexa_access_token = str(uuid1())

    channel = Channel(
        channel_type='alexa',
        channel_user_id=alexa_access_token,
        user_id=user_id,
        push_enabled=False,
    )

    UserTable.upsert(User(user_id=user_id))
    ChannelTable.upsert(channel)

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
