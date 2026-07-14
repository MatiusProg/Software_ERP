from django.apps import AppConfig


class CatalogoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalogo"
    verbose_name = "Catálogo"

    def ready(self):
        # Conecta las señales que llenan el historial de precios.
        from . import senales  # noqa: F401
