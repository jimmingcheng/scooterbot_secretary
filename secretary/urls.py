from django.urls import re_path
from django_ask_sdk.skill_adapter import SkillAdapter

from secretary.alexa import get_skill_builder
from secretary.views import login
from secretary.views import read
from secretary.views import webhooks


urlpatterns = [
    re_path(r'^login$', login.step1),
    re_path(r'^login/step2$', login.step2),
    re_path(r'^login/step3$', login.step3),
    re_path(r'^login/step4$', login.step4),
    re_path(r'^login/alexa$', login.alexa_step1),
    re_path(r'^login/alexa/step2$', login.alexa_step2),
    re_path(r'webhooks/add_todo$', webhooks.add_todo),
    re_path(r'^alexa$', SkillAdapter.as_view(
        skill=get_skill_builder().create(),
        verify_signature=False,
        verify_timestamp=False,
    )),
    re_path(r'^todos$', read.get_todos_for_day),
]
