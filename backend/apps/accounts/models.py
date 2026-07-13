"""
Núcleo de identidad y tenancy.

- ``Organization``: el tenant (un negocio/cliente que paga la suscripción).
- ``User``: login por email; puede pertenecer a varias organizaciones.
- ``Membership``: relación User↔Organization con un rol dentro de esa org.
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel
from .managers import UserManager


class Organization(TimeStampedModel):
    """Tenant. Todos los datos de negocio cuelgan de una organización."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Usuario con email como identificador. Sin ``username``."""

    username = None
    email = models.EmailField(_("email address"), unique=True)
    full_name = models.CharField(max_length=150, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class Membership(TimeStampedModel):
    """Pertenencia de un usuario a una organización, con su rol."""

    class Role(models.TextChoices):
        OWNER = "owner", "Propietario"
        ADMIN = "admin", "Administrador"
        SELLER = "seller", "Vendedor"
        VIEWER = "viewer", "Solo lectura"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OWNER)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"], name="unique_membership"
            )
        ]

    def __str__(self):
        return f"{self.user} @ {self.organization} ({self.role})"
