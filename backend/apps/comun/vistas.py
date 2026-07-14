"""
Base de vistas para modelos multi-tenant.

``TenantModelViewSet`` da CRUD completo sobre un modelo que hereda de
``ModeloTenant``, aplicando el permiso por rol y el aislamiento por organización.

IMPORTANTE sobre el aislamiento: el ``queryset`` de clase de un ViewSet se evalúa
al importar el módulo, cuando todavía no hay organización activa, por lo que el
filtro implícito del manager NO queda aplicado. Por eso aquí se re-filtra por la
organización del request en cada llamada (``get_queryset``). Las subclases definen
``queryset`` (con sus ``select_related``/``prefetch_related``) y
``serializer_class``; opcionalmente ``filterset_fields``, ``search_fields`` y
``ordering_fields`` (los backends de filtro/búsqueda/orden son globales).
"""

from rest_framework import viewsets

from apps.cuentas.permisos import SoloLecturaOAdmin
from .tenancy import get_organizacion_actual


class TenantModelViewSet(viewsets.ModelViewSet):
    """CRUD para modelos del tenant activo. Lectura para cualquier miembro;
    escritura solo propietario/admin."""

    permission_classes = [SoloLecturaOAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        org = getattr(self.request, "organizacion", None) or get_organizacion_actual()
        if org is None:
            return qs.none()
        return qs.filter(organizacion=org)
