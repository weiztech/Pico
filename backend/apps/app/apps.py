from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.app"
    label = "access_app"


# uv run python manage.py dumpdata access_app --indent 4 > access_app.json
