import json
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from urllib.parse import quote
from urllib.parse import unquote
from uuid import uuid1

from secretary.database import UserTable
from secretary.google_apis import get_userdb_client


USE_GOOGLE_APIS_USER_ID = 'use_google_apis_user_id'


def oauth(request: HttpRequest) -> HttpResponse:
    user_id = request.GET.get('u', USE_GOOGLE_APIS_USER_ID)

    url = get_userdb_client().get_authorization_url(
        redirect_url='https://secretary.scooterbot.org/oauth/callback',
        access_type='offline',
        state=user_id,
    )
    return HttpResponseRedirect(url)


def oauth_callback(request: HttpRequest) -> HttpResponse:
    code = request.GET['code']
    user_id = request.GET['state']

    google_apis_user_id = get_userdb_client().save_user_and_credentials(code)

    if user_id == USE_GOOGLE_APIS_USER_ID:
        user_id = google_apis_user_id

    return HttpResponseRedirect(
        'https://secretary.scooterbot.org/calendars'
        f'?user_id={user_id}&google_apis_user_id={google_apis_user_id}'
    )


def alexa_oauth(request: HttpRequest) -> HttpResponse:
    alexa_state = request.GET['state']
    alexa_redirect_uri = request.GET['redirect_uri']

    state = _pack_alexa_state(alexa_state, alexa_redirect_uri)

    url = get_userdb_client().get_authorization_url(
        state=state,
        redirect_url='https://secretary.scooterbot.org/alexa_oauth/callback',
        access_type='offline',
    )

    return HttpResponseRedirect(url)


def alexa_oauth_callback(request: HttpRequest) -> HttpResponse:
    code = request.GET['code']
    state = request.GET['state']

    google_apis_user_id = get_userdb_client().save_user_and_credentials(code)

    url = _save_alexa_user_and_redirect(google_apis_user_id, state)

    return HttpResponseRedirect(url)


def _save_alexa_user_and_redirect(google_apis_user_id: str, state: str) -> str:
    alexa_state, alexa_redirect_uri = _unpack_alexa_state(state)
    alexa_access_token = str(uuid1())

    UserTable().upsert(alexa_access_token, google_apis_user_id, 'qrvfc4qvfm5d2kh0m6g9euo4s8@group.calendar.google.com')

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
