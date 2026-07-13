"""
Auditoría en dos tablas:

- ``Bitacora``: cabecera del evento (quién / qué acción / sobre qué / cuándo).
- ``BitacoraDetalle``: un registro por cada campo modificado (valor anterior/nuevo).
"""

from django.db import models


class Bitacora(models.Model):
    class Accion(models.TextChoices):
        CREAR = "crear", "Crear"
        ACTUALIZAR = "actualizar", "Actualizar"
        ELIMINAR = "eliminar", "Eliminar"
        LOGIN = "login", "Inicio de sesión"
        LOGOUT = "logout", "Cierre de sesión"
        LOGIN_FALLIDO = "login_fallido", "Inicio de sesión fallido"

    organizacion = models.ForeignKey(
        "cuentas.Organizacion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bitacoras",
        verbose_name="organización",
    )
    usuario = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bitacoras",
    )
    accion = models.CharField(max_length=20, choices=Accion.choices)
    modelo = models.CharField(max_length=100, blank=True)
    objeto_id = models.CharField(max_length=100, blank=True)
    objeto_desc = models.CharField("descripción del objeto", max_length=255, blank=True)
    descripcion = models.CharField("descripción", max_length=255, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bitacora"
        ordering = ["-fecha"]
        verbose_name = "bitácora"
        verbose_name_plural = "bitácoras"
        indexes = [
            models.Index(fields=["organizacion", "-fecha"]),
            models.Index(fields=["modelo", "objeto_id"]),
        ]

    def __str__(self):
        return f"[{self.fecha:%Y-%m-%d %H:%M}] {self.accion} {self.modelo} por {self.usuario}"


class BitacoraDetalle(models.Model):
    bitacora = models.ForeignKey(
        Bitacora, on_delete=models.CASCADE, related_name="detalles"
    )
    campo = models.CharField(max_length=100)
    valor_anterior = models.TextField(blank=True, null=True)
    valor_nuevo = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "bitacora_detalle"
        verbose_name = "detalle de bitácora"
        verbose_name_plural = "detalles de bitácora"

    def __str__(self):
        return f"{self.campo}: {self.valor_anterior} → {self.valor_nuevo}"
