"""
Terceros: clientes, proveedores y transportadoras (un mismo tercero puede ser
varios a la vez, de ahí los flags booleanos en lugar de un único campo tipo).

Contactos y ubicaciones son tablas hijas: un tercero puede tener varios de cada
uno (varios teléfonos, sucursales, etc.).
"""

from django.db import models

from apps.comun.models import ModeloTenant


class Tercero(ModeloTenant):
    nombre = models.CharField(max_length=200)
    nit_ci = models.CharField("NIT/CI", max_length=30, blank=True)
    es_cliente = models.BooleanField("es cliente", default=False)
    es_proveedor = models.BooleanField("es proveedor", default=False)
    es_transportadora = models.BooleanField("es transportadora", default=False)
    notas = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "tercero"
        ordering = ["nombre"]
        verbose_name = "tercero"
        verbose_name_plural = "terceros"
        indexes = [
            models.Index(fields=["organizacion", "nombre"]),
        ]

    def __str__(self):
        return self.nombre


class ContactoTercero(ModeloTenant):
    class Tipo(models.TextChoices):
        TELEFONO = "telefono", "Teléfono"
        EMAIL = "email", "Email"
        WHATSAPP = "whatsapp", "WhatsApp"

    tercero = models.ForeignKey(
        Tercero, on_delete=models.CASCADE, related_name="contactos"
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.TELEFONO)
    valor = models.CharField(max_length=150)

    class Meta:
        db_table = "contacto_tercero"
        verbose_name = "contacto"
        verbose_name_plural = "contactos"

    def __str__(self):
        return f"{self.tipo}: {self.valor}"


class UbicacionTercero(ModeloTenant):
    tercero = models.ForeignKey(
        Tercero, on_delete=models.CASCADE, related_name="ubicaciones"
    )
    direccion = models.CharField("dirección", max_length=255, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    referencia = models.CharField(max_length=255, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = "ubicacion_tercero"
        verbose_name = "ubicación"
        verbose_name_plural = "ubicaciones"

    def __str__(self):
        return f"{self.direccion}, {self.ciudad}".strip(", ")
