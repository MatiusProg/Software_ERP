from rest_framework.decorators import action
from rest_framework.response import Response

from apps.comun.vistas import TenantModelViewSet
from .models import Categoria, Producto
from .serializers import (
    CategoriaSerializer,
    HistorialPrecioSerializer,
    ProductoSerializer,
)


class CategoriaViewSet(TenantModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    search_fields = ["nombre", "descripcion"]
    ordering_fields = ["nombre", "creado_en"]


class ProductoViewSet(TenantModelViewSet):
    queryset = Producto.objects.select_related("categoria").all()
    serializer_class = ProductoSerializer
    filterset_fields = ["categoria", "unidad", "es_servicio", "activo"]
    search_fields = ["sku", "codigo_barras", "nombre"]
    ordering_fields = ["nombre", "sku", "precio_venta", "stock", "creado_en"]

    @action(detail=True, methods=["get"])
    def historial_precios(self, request, pk=None):
        """Historial de cambios de precio de un producto (paginado)."""
        producto = self.get_object()
        qs = producto.historial_precios.all()
        page = self.paginate_queryset(qs)
        serializer = HistorialPrecioSerializer(page if page is not None else qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)
