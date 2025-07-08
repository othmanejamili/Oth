from django.apps import AppConfig


class EcommConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Ecomm'

    def ready(self):
        import Ecomm.signals
