from django.urls import re_path

from secretary.views import private


urlpatterns = [
    re_path(r'^send_message_to_agent$', private.send_message_to_agent),
]
