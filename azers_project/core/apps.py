from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        import core.signals  #  make sure signals.py is in your core app


# from django.apps import AppConfig


# class CoreConfig(AppConfig):
#     default_auto_field = "django.db.models.BigAutoField"
#     name = "core"
