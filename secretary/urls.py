from django.urls import path
from django.urls import re_path
from django_ask_sdk.skill_adapter import SkillAdapter
from django.views.generic import TemplateView

from secretary.alexa import get_skill_builder
from secretary.views import login
from secretary.views import read
from secretary.views import twilio
from secretary.views import webhooks


REACT = TemplateView.as_view(template_name='index.html')

urlpatterns = [
    path('', REACT),
    path('signup', REACT),
    path('privacy', REACT),
    path('tos', REACT),
    re_path(r'^login$', REACT),
    re_path(r'^login/step2$', login.step2),
    re_path(r'^login/step3$', login.step3),
    re_path(r'^login/step4$', REACT),
    re_path(r'^login/step4/calendar_list$', login.step4_calendar_list),
    re_path(r'^login/step5$', login.step5),
    re_path(r'^login/alexa$', login.alexa_step1),
    re_path(r'^login/alexa/step2$', login.alexa_step2),
    re_path(r'webhooks/add_todo$', webhooks.add_todo),
    re_path(r'^alexa$', SkillAdapter.as_view(
        skill=get_skill_builder().create(),
        verify_signature=False,
        verify_timestamp=False,
    )),
    re_path(r'^todos$', read.get_todos_for_day),
    re_path(r'^twilio/sms_reply$', twilio.sms_reply),
]
