"""
Modelos base reutilizables.

- ``ModeloConFechas``: campos de creación/actualización automáticos.
- ``ModeloTenant``: base para TODO modelo de negocio. Lleva FK ``organizacion``
  y un manager que filtra por la organización activa del request, de modo que el
  aislamiento entre tenants es el comportamiento por defecto.
"""

from django.db import models

from .tenancy import get_organizacion_actual


class ModeloConFechas(models.Model):
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantManager(models.Manager):
    """Filtra por la organización activa. Usa ``todos`` para saltarte el filtro
    (migraciones, tareas de sistema, admin cruzado)."""

    def get_queryset(self):
        qs = super().get_queryset()
        organizacion = get_organizacion_actual()
        if organizacion is not None:
            return qs.filter(organizacion=organizacion)
        return qs


class ModeloTenant(ModeloConFechas):
    organizacion = models.ForeignKey(
        "cuentas.Organizacion",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
        verbose_name="organización",
    )

    # ``objects`` está scopeado al tenant activo; ``todos`` no filtra.
    objects = TenantManager()
    todos = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Si no se asignó organización explícita, hereda la del request activo.
        if self.organizacion_id is None:
            actual = get_organizacion_actual()
            if actual is not None:
                self.organizacion = actual
        super().save(*args, **kwargs)
