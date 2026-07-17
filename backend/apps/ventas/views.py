"""
Vistas de ventas, cotizaciones y listas.

Todas heredan de ``TenantModelViewSet`` (aislamiento por organización) pero usan
el permiso ``MiembroEscribeAdminBorra``: el vendedor puede crear/editar en su día
a día; solo propietario/admin pueden borrar.
"""

from decimal import Decimal

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.comun.vistas import TenantModelViewSet
from apps.cuentas.permisos import MiembroEscribeAdminBorra
from .models import (
    Cotizacion, Venta, VentaDetalle, Lista, siguiente_numero,
)
from .serializers import CotizacionSerializer, VentaSerializer, ListaSerializer

CERO = Decimal("0")


class CotizacionViewSet(TenantModelViewSet):
    permission_classes = [MiembroEscribeAdminBorra]
    queryset = Cotizacion.objects.select_related("cliente").prefetch_related("detalles").all()
    serializer_class = CotizacionSerializer
    filterset_fields = ["estado", "cliente"]
    search_fields = ["numero", "cliente_nombre"]
    ordering_fields = ["creado_en", "numero", "total"]

    @action(detail=True, methods=["post"])
    def convertir_en_venta(self, request, pk=None):
        """Genera una venta a partir de la cotización (copia las líneas y marca la
        cotización como aceptada)."""
        cotizacion = self.get_object()
        org = cotizacion.organizacion
        with transaction.atomic():
            venta = Venta.objects.create(
                organizacion=org,
                numero=siguiente_numero(org, "venta", "V"),
                cliente=cotizacion.cliente,
                cliente_nombre=cotizacion.cliente_nombre,
                cotizacion_origen=cotizacion,
                notas=cotizacion.notas,
            )
            total = impuesto = CERO
            for d in cotizacion.detalles.all():
                linea = VentaDetalle.objects.create(
                    organizacion=org, venta=venta,
                    producto=d.producto, descripcion=d.descripcion, detalle=d.detalle,
                    cantidad=d.cantidad, precio_unitario=d.precio_unitario,
                    impuesto=d.impuesto, total=d.total, orden=d.orden,
                )
                total += linea.calcular_total()
                impuesto += linea.impuesto_monto
            venta.subtotal = total - impuesto
            venta.impuesto_total = impuesto
            venta.total = total
            venta.save(update_fields=["subtotal", "impuesto_total", "total"])
            cotizacion.estado = Cotizacion.Estado.ACEPTADA
            cotizacion.save(update_fields=["estado"])
        serializer = VentaSerializer(venta, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VentaViewSet(TenantModelViewSet):
    permission_classes = [MiembroEscribeAdminBorra]
    queryset = Venta.objects.select_related("cliente", "cotizacion_origen").prefetch_related("detalles").all()
    serializer_class = VentaSerializer
    filterset_fields = ["estado", "estado_pago", "cliente"]
    search_fields = ["numero", "cliente_nombre"]
    ordering_fields = ["creado_en", "numero", "total"]


class ListaViewSet(TenantModelViewSet):
    permission_classes = [MiembroEscribeAdminBorra]
    queryset = Lista.objects.select_related("cliente").prefetch_related("items").all()
    serializer_class = ListaSerializer
    filterset_fields = ["estado", "cliente"]
    search_fields = ["titulo", "cliente_nombre"]
    ordering_fields = ["creado_en", "titulo", "total"]
