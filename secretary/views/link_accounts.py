from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from oauth_userdb.client import OAuthUserDBClient
from sb_service_util.account_links import AccountLinkRequest

from secretary.account_linking import get_account_link_manager
from secretary.google_apis import get_oauth_client


def oauth_client() -> OAuthUserDBClient:
    return get_oauth_client(
        redirect_url='https://secretary.scooterbot.ai/link_accounts/step2',
    )


def step1(request: HttpRequest) -> HttpResponse:
    remote_account_type = request.GET['a']
    remote_user_id = request.GET['u']
    token = request.GET['t']

    link_request = AccountLinkRequest(
        remote_account_type=remote_account_type,
        remote_user_id=remote_user_id,
        token=token,
    )

    url = oauth_client().get_authorization_url(
        access_type='offline',
        state=link_request.pack(),
        prompt='consent',
    )

    return HttpResponseRedirect(url)


def step2(request: HttpRequest) -> HttpResponse:
    code = request.GET['code']
    link_request = AccountLinkRequest.unpack(request.GET['state'])

    user_id = oauth_client().save_user_and_credentials(code)

    try:
        get_account_link_manager().process_link_request(user_id, link_request)
        return HttpResponse('Accounts linked successfully')
    except Exception:
        return HttpResponse('Token is invalid or expired')
