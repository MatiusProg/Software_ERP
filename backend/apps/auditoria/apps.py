from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.auditoria"
    verbose_name = "Auditoría"

    def ready(self):
        from django.apps import apps
        from .registry import auditar

        # Modelos a auditar automáticamente (se irán agregando por fase).
        etiquetas = [
            ("cuentas", "Organizacion"),
            ("cuentas", "Usuario"),
            ("cuentas", "Membresia"),
            ("catalogo", "Categoria"),
            ("catalogo", "Producto"),
            ("terceros", "Tercero"),
            ("ventas", "Cotizacion"),
            ("ventas", "Venta"),
            ("ventas", "VentaDetalle"),
        ]
        for app_label, model_name in etiquetas:
            try:
                auditar(apps.get_model(app_label, model_name))
            except LookupError:
                pass
