from django.urls import path
from django_ask_sdk.skill_adapter import SkillAdapter

from secretary.alexa import get_skill_builder
from secretary.views import account
from secretary.views import link_accounts
from secretary.views import setup
from secretary.views import setup_alexa
from secretary.views import twilio
from secretary.views.base import static_view
from secretary.views.home import HomePage
from secretary.views.privacy_policy import PrivacyPolicyPage
from secretary.views.signup import SignupPage
from secretary.views.tos import TermsOfServicePage


urlpatterns = [
    # Static pages
    path('', static_view(HomePage)),
    path('signup', static_view(SignupPage)),
    path('privacy', static_view(PrivacyPolicyPage)),
    path('tos', static_view(TermsOfServicePage)),

    # Endpoints
    path('account/remove', account.remove_account),
    path('account/remove/confirm', account.confirm_remove_account),
    path('link_accounts', link_accounts.step1),
    path('link_accounts/step2', link_accounts.step2),
    path('setup', setup.splash),
    path('setup/step1', setup.step1),
    path('setup/step2', setup.step2),
    path('setup/alexa/step1', setup_alexa.step1),
    path('setup/alexa/step2', setup_alexa.step2),
    path('twilio/sms_reply', twilio.sms_reply),

    # Alexa skill endpoint
    path('alexa', SkillAdapter.as_view(
        skill=get_skill_builder().create(),
        verify_signature=False,
        verify_timestamp=False,
    )),
]
