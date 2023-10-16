from django.urls import re_path
from django_ask_sdk.skill_adapter import SkillAdapter

from secretary.alexa import get_skill_builder
from secretary.views import calendar
from secretary.views import login
from secretary.views import read
from secretary.views import webhooks


urlpatterns = [
    re_path(r'^login$', login.oauth),
    re_path(r'^oauth/callback$', login.oauth_callback),
    re_path(r'^alexa_oauth$', login.alexa_oauth),
    re_path(r'^alexa_oauth/callback$', login.alexa_oauth_callback),
    re_path(r'^calendars$', calendar.show_calendar_options),
    re_path(r'^calendar$', calendar.save_calendar),
    re_path(r'webhooks/add_todo$', webhooks.add_todo),
    re_path(r'^alexa$', SkillAdapter.as_view(
        skill=get_skill_builder().create(),
        verify_signature=False,
        verify_timestamp=False,
    )),
    re_path(r'^todos$', read.get_todos_for_day),
]
