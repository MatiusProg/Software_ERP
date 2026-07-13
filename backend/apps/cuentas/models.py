"""
Núcleo de identidad y tenancy.

- ``Organizacion``: el tenant (un negocio/cliente que paga la suscripción).
- ``Usuario``: login por email; puede pertenecer a varias organizaciones.
- ``Membresia``: relación Usuario↔Organizacion con un rol dentro de esa org.
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.comun.models import ModeloConFechas
from .managers import UsuarioManager


class Organizacion(ModeloConFechas):
    """Tenant. Todos los datos de negocio cuelgan de una organización."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = "organizacion"
        ordering = ["nombre"]
        verbose_name = "organización"
        verbose_name_plural = "organizaciones"

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    """Usuario con email como identificador. Sin ``username``."""

    username = None
    email = models.EmailField("correo", unique=True)
    nombre_completo = models.CharField("nombre completo", max_length=150, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    class Meta:
        db_table = "usuario"
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.email


class Membresia(ModeloConFechas):
    """Pertenencia de un usuario a una organización, con su rol."""

    class Rol(models.TextChoices):
        PROPIETARIO = "propietario", "Propietario"
        ADMIN = "admin", "Administrador"
        VENDEDOR = "vendedor", "Vendedor"
        LECTURA = "lectura", "Solo lectura"

    organizacion = models.ForeignKey(
        Organizacion,
        on_delete=models.CASCADE,
        related_name="membresias",
        verbose_name="organización",
    )
    usuario = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.CASCADE,
        related_name="membresias",
    )
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.PROPIETARIO)

    class Meta:
        db_table = "membresia"
        verbose_name = "membresía"
        verbose_name_plural = "membresías"
        constraints = [
            models.UniqueConstraint(
                fields=["organizacion", "usuario"], name="membresia_unica"
            )
        ]

    def __str__(self):
        return f"{self.usuario} @ {self.organizacion} ({self.rol})"
