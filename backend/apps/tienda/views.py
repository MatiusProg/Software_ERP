"""
Escaparate público: navegar el catálogo de un negocio por su ``slug``, sin login.

Estas vistas son la base del "modo tienda que no pierde simplicidad": un visitante
anónimo ve el catálogo; registrarse suma funciones (sincronizar listas, pedir, etc.),
nunca es un requisito para mirar.

Notas de seguridad/tenancy:
- Son públicas: ``AllowAny`` y sin autenticación (se desactiva el JWT global).
- El aislamiento NO viene del tenant activo (no hay usuario), sino del ``slug`` en la
  URL. Por eso se usa el manager ``todos`` (sin filtro implícito) y se filtra a mano
  por la organización resuelta desde el slug.
- Solo organizaciones activas y solo productos ``activo=True``.
"""

from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.catalogo.models import Categoria, Producto
from apps.cuentas.models import Organizacion
from .serializers import (
    TiendaOrganizacionSerializer,
    TiendaCategoriaSerializer,
    TiendaProductoSerializer,
)


class _TiendaPublicaMixin:
    authentication_classes = []       # sin JWT: endpoint público
    permission_classes = [AllowAny]

    def _organizacion(self):
        return get_object_or_404(Organizacion, slug=self.kwargs["slug"], activa=True)


class TiendaInfoView(_TiendaPublicaMixin, generics.RetrieveAPIView):
    """Datos públicos del negocio."""

    serializer_class = TiendaOrganizacionSerializer

    def get_object(self):
        return self._organizacion()


class TiendaCategoriasView(_TiendaPublicaMixin, generics.ListAPIView):
    serializer_class = TiendaCategoriaSerializer
    search_fields = ["nombre"]

    def get_queryset(self):
        return Categoria.todos.filter(organizacion=self._organizacion()).order_by("nombre")


class TiendaProductosView(_TiendaPublicaMixin, generics.ListAPIView):
    serializer_class = TiendaProductoSerializer
    filterset_fields = ["categoria", "es_servicio"]
    search_fields = ["nombre", "sku", "codigo_barras"]
    ordering_fields = ["nombre", "precio_venta"]

    def get_queryset(self):
        return (
            Producto.todos
            .filter(organizacion=self._organizacion(), activo=True)
            .select_related("categoria")
            .order_by("nombre")
        )
