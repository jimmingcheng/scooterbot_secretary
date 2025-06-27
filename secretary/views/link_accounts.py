import json
from dataclasses import dataclass

from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from urllib.parse import quote
from urllib.parse import unquote

from secretary.account_linking import make_token
from secretary.database import AccountLink
from secretary.database import AccountLinkTable
from secretary.google_apis import get_userdb_client


@dataclass
class OAuthState:
    other_account_type: str
    other_user_id: str
    account_linking_token: str

    def pack(self) -> str:
        return quote(json.dumps({
            'other_account_type': self.other_account_type,
            'other_user_id': self.other_user_id,
            'account_linking_token': self.account_linking_token,
        }))

    @classmethod
    def unpack(cls, state: str) -> 'OAuthState':
        unpacked = json.loads(unquote(state))
        return OAuthState(
            other_account_type=unpacked['other_account_type'],
            other_user_id=unpacked['other_user_id'],
            account_linking_token=unpacked['account_linking_token'],
        )


def step1(request: HttpRequest) -> HttpResponse:
    other_account_type = request.GET['a']
    other_user_id = request.GET['u']
    account_linking_token = request.GET['t']

    url = get_userdb_client(
        redirect_url='https://secretary.scooterbot.ai/link_accounts/step2',
    ).get_authorization_url(
        access_type='offline',
        state=OAuthState(
            other_account_type=other_account_type,
            other_user_id=other_user_id,
            account_linking_token=account_linking_token,
        ).pack(),
        prompt='consent',
    )
    return HttpResponseRedirect(url)


def step2(request: HttpRequest) -> HttpResponse:
    code = request.GET['code']
    state = OAuthState.unpack(request.GET['state'])

    user_id = get_userdb_client().save_user_and_credentials(code)

    if make_token(state.other_user_id) == state.account_linking_token:
        AccountLinkTable.upsert(
            AccountLink(
                user_id=user_id,
                other_account_type=state.other_account_type,
                other_user_id=state.other_user_id,
            )
        )
        return HttpResponse('Your accounts have been successfully linked.')
    else:
        return HttpResponse('Your account linking request has expired. Please try again.')
