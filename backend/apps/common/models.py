"""
Modelos base reutilizables.

- ``TimeStampedModel``: created/updated automáticos.
- ``TenantModel``: base para TODO modelo de negocio. Lleva FK ``organization``
  y un manager que filtra por la organización activa del request, de modo que
  el aislamiento entre tenants es el comportamiento por defecto, no algo que
  cada vista deba recordar.
"""

from django.db import models

from .tenancy import get_current_organization


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantManager(models.Manager):
    """Filtra por la organización activa. Usa ``all_objects`` para saltarte
    el filtro (migraciones, tareas de sistema, admin cruzado)."""

    def get_queryset(self):
        qs = super().get_queryset()
        organization = get_current_organization()
        if organization is not None:
            return qs.filter(organization=organization)
        return qs


class TenantModel(TimeStampedModel):
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    # ``objects`` está scopeado al tenant activo; ``all_objects`` no filtra.
    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Si no se asignó organización explícita, hereda la del request activo.
        if self.organization_id is None:
            current = get_current_organization()
            if current is not None:
                self.organization = current
        super().save(*args, **kwargs)
