from django.http import HttpRequest
from django.http import HttpResponse

from secretary import account
from secretary.account_linking import get_account_link_manager


def remove_account(request: HttpRequest) -> HttpResponse:
    user_id = request.GET['u']
    token = request.GET['t']

    if get_account_link_manager().make_token('secretary', user_id) == token:
        return HttpResponse(
            '<a href="/account/remove/confirm?user_id={user_id}&t={t}">Click here</a> to confirm account removal.'.format(
                user_id=user_id,
                t=token,
            )
        )
    else:
        return HttpResponse('Your account removal request has expired.')


def confirm_remove_account(request: HttpRequest) -> HttpResponse:
    user_id = request.GET['user_id']
    token = request.GET['t']

    if get_account_link_manager().make_token('secretary', user_id) == token:
        account.remove_account(user_id)

        return HttpResponse('Your account has been successfully removed.')
    else:
        return HttpResponse('Your account removal request has expired.')
