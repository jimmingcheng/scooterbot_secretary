from django.apps import AppConfig


class TodoConfig(AppConfig):
    name = 'secretary'
    verbose_name = 'Secretary'

    def ready(self):
        from secretary.config import load_all_configs
        from secretary import logger

        load_all_configs()
        logger.init('secretary')
