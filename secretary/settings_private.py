from secretary.settings import *  # noqa


ROOT_URLCONF = 'secretary.urls_private'
ALLOWED_HOSTS = ['secretary-private']
ASGI_APPLICATION = 'secretary.asgi_private.application'
