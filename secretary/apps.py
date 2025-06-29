from django.apps import AppConfig


class TodoConfig(AppConfig):
    name = 'secretary'
    verbose_name = 'Secretary'

    def ready(self):
        import secretary
        secretary.init()
