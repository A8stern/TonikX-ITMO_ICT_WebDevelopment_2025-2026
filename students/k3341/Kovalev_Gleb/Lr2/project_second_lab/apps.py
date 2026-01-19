from django.apps import AppConfig

class ProjectSecondLabConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "project_second_lab"

    def ready(self):
        import project_second_lab.signals  # noqa