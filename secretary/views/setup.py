from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from oauth_userdb.client import OAuthUserDBClient
from urllib.parse import quote
from urllib.parse import unquote

from secretary.data_models import Channel
from secretary.data_models import User
from secretary.google_apis import get_oauth_client
from secretary.notifications import notify
from secretary.views.base import HTMLPage


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


def splash(request: HttpRequest) -> HttpResponse:
    return HttpResponse(
        SplashPage(
            discord_user_id=request.GET.get('du'),
            sms_number=request.GET.get('sms')
        ).render()
    )


def step1(request: HttpRequest) -> HttpResponse:
    discord_user_id = request.GET.get('discord_user_id')
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
        Channel.upsert(
            Channel(
                channel_type='discord',
                channel_user_id=state.discord_user_id,
                user_id=user_id,
                push_enabled=True,
            )
        )
    if state.sms_number:
        Channel.upsert(
            Channel(
                channel_type='sms',
                channel_user_id=state.sms_number,
                user_id=user_id,
                push_enabled=True,
            )
        )

    await notify(user_id, "You're all set!")

    return HttpResponse("You're all set!")


class SplashPage(HTMLPage):
    discord_user_id: str | None = None
    sms_number: str | None = None

    def __init__(
        self,
        discord_user_id: str | None = None,
        sms_number: str | None = None,
    ) -> None:
        super().__init__()
        self.discord_user_id = discord_user_id
        self.sms_number = sms_number

    def content(self) -> str:
        return textwrap.dedent(
            """\
            <h1>Connect your Google account</h1>

            <div class="login_disclaimer">
                <h2>Your Privacy</h2>

                <p>In order to provide useful services as your Secretary, we'll access some of your private data such as:</p>

                <ul>
                    <li>The natural language requests you submit directly to Scooterbot AI during chats</li>
                    <li>Your Google Calendar events and schedules</li>
                </ul>

                <p>Your privacy is important to us, and here's how we'll use it:</p>

                <h3>Use of Data</h3>
                <p>The data we collect is solely used for fulfilling tasks on your calendar such as reading your schedule and creating events. This includes:</p>
                <ul>
                    <li>When send a message to your Secretary, we'll forward the message text to ChatGPT, a 3rd party AI owned by OpenAI.</li>
                    <li>After OpenAI interprets your message, we'll use the interpreted instructions to read or write to your Google Calendar on your behalf.</li>
                    <li>In some cases, the specific Google Calendar data you request will be sent back to ChatGPT for further interpretation.</li>
                </ul>

                <h3>Disclosure of Data</h3>
                <p>We may send your data to a third-party AI (OpenAI) for interpreting natural language requests. OpenAI may retain your data for up to 30 days to identify abuse, but will not otherwise retain your data or use it for any other purpose than to provide responses to your requests. Besides this, your data remains confidential and won't be sold, distributed, leased, or disclosed to other third parties unless we have your permission or are required by law to do so.</p>

                <p>By clicking "Connect Google Calendar", you agree to the above terms, as well as our <a href="/privacy">Privacy Policy</a> and <a href="/tos">Terms of Service</a></p>
            </div>

            <form action="/setup/step1" method="GET">
                <input type="hidden" name="discord_user_id" value="{discord_user_id}" />
                <input type="hidden" name="sms" value="{sms_number}" />
                <button type="submit" class="login">
                    <img src="/static/gcal_logo.png" alt="Google Calendar Logo" />
                    Connect Google Calendar
                </button>
            </form>
            """
        ).format(
            discord_user_id=self.discord_user_id or '',
            sms_number=self.sms_number or '',
        )
