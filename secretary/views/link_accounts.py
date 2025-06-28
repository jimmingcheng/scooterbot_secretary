from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from scooterbot_account_linking import AccountLinkRequest
from scooterbot_account_linking import TokenInvalidOrExpiredError

from secretary.account_linking import get_account_link_manager
from secretary.google_apis import get_userdb_client


def step1(request: HttpRequest) -> HttpResponse:
    remote_account_type = request.GET['a']
    remote_user_id = request.GET['u']
    token = request.GET['t']

    link_request = AccountLinkRequest(
        remote_account_type=remote_account_type,
        remote_user_id=remote_user_id,
        token=token,
    )

    url = get_userdb_client(
        redirect_url='https://secretary.scooterbot.ai/link_accounts/step2',
    ).get_authorization_url(
        access_type='offline',
        state=link_request.pack(),
        prompt='consent',
    )

    return HttpResponseRedirect(url)


def step2(request: HttpRequest) -> HttpResponse:
    code = request.GET['code']
    link_request = AccountLinkRequest.unpack(request.GET['state'])

    user_id = get_userdb_client().save_user_and_credentials(code)

    try:
        get_account_link_manager().process_link_request(user_id, link_request)
        return HttpResponse('Accounts linked successfully')
    except TokenInvalidOrExpiredError:
        return HttpResponse('Token is invalid or expired')
