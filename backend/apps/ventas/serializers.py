"""
Serializers de ventas, cotizaciones y listas.

Los tres comparten el patrón cabecera + líneas anidadas (escribibles). Al
crear/actualizar, las líneas se recrean una por una (no en bloque) para que la
auditoría por señales alcance a ``VentaDetalle``; luego se recalculan los totales
de la cabecera. El número correlativo (V-0001, COT-0001) se asigna en el servidor.
"""

from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.comun.tenancy import get_organizacion_actual
from .models import (
    Cotizacion, CotizacionDetalle,
    Venta, VentaDetalle,
    Lista, ListaItem,
    siguiente_numero,
)

CERO = Decimal("0")


# --------------------------------------------------------------------------- #
# Serializers de línea
# --------------------------------------------------------------------------- #
class _LineaSerializerBase(serializers.ModelSerializer):
    # ``descripcion`` puede venir vacía si hay ``producto`` (se autocompleta).
    descripcion = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        # En un PATCH parcial cada línea es completa (se reemplazan todas), así que
        # aquí ``attrs`` siempre trae la línea entera.
        producto = attrs.get("producto")
        descripcion = (attrs.get("descripcion") or "").strip()
        if not descripcion and producto is None:
            raise serializers.ValidationError(
                "Cada línea necesita una descripción o un producto."
            )
        cantidad = attrs.get("cantidad")
        precio_unitario = attrs.get("precio_unitario")
        # Modo unitario: o van ambos, o ninguno.
        if (cantidad is None) != (precio_unitario is None):
            raise serializers.ValidationError(
                "Para el modo unitario indica cantidad y precio unitario juntos."
            )
        return attrs


class CotizacionDetalleSerializer(_LineaSerializerBase):
    impuesto = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True
    )
    impuesto_monto = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = CotizacionDetalle
        fields = [
            "id", "producto", "descripcion", "detalle",
            "cantidad", "precio_unitario", "impuesto",
            "total", "impuesto_monto", "orden",
        ]


class VentaDetalleSerializer(_LineaSerializerBase):
    impuesto = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True
    )
    impuesto_monto = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = VentaDetalle
        fields = [
            "id", "producto", "descripcion", "detalle",
            "cantidad", "precio_unitario", "impuesto",
            "total", "impuesto_monto", "orden",
        ]


class ListaItemSerializer(_LineaSerializerBase):
    class Meta:
        model = ListaItem
        fields = [
            "id", "producto", "descripcion", "detalle",
            "cantidad", "precio_unitario", "total", "orden", "comprado",
        ]


# --------------------------------------------------------------------------- #
# Mixin de cabecera con líneas anidadas
# --------------------------------------------------------------------------- #
class _DocumentoConLineasMixin:
    """create/update de líneas anidadas + recálculo de totales.

    Las subclases definen:
    - ``modelo_linea``: modelo hijo (CotizacionDetalle, VentaDetalle, ListaItem).
    - ``campo_lineas``: nombre del campo anidado y del ``related_name`` (coinciden).
    - ``campo_fk``: nombre del FK del hijo hacia la cabecera.
    - ``fiscal``: si maneja impuesto/subtotal (cotización y venta) o solo total (lista).
    - ``tipo_secuencia`` / ``prefijo``: para el número correlativo (None en listas).
    """

    modelo_linea = None
    campo_lineas = "detalles"
    campo_fk = None
    fiscal = True
    tipo_secuencia = None
    prefijo = ""

    def _org(self):
        req = self.context.get("request")
        return getattr(req, "organizacion", None) or get_organizacion_actual()

    def _crear_lineas(self, cabecera, lineas_data):
        for i, data in enumerate(lineas_data):
            data = dict(data)
            data.setdefault("orden", i)
            if not (data.get("descripcion") or "").strip() and data.get("producto"):
                data["descripcion"] = data["producto"].nombre
            if self.fiscal and data.get("impuesto") is None and data.get("producto"):
                data["impuesto"] = data["producto"].impuesto
            linea = self.modelo_linea(
                organizacion=cabecera.organizacion,
                **{self.campo_fk: cabecera},
                **data,
            )
            linea.total = linea.calcular_total()
            linea.save()  # individual → dispara auditoría donde el modelo está registrado

    def _recalcular_totales(self, cabecera):
        lineas = list(getattr(cabecera, self.campo_lineas).all())
        total = sum((l.calcular_total() for l in lineas), CERO)
        if self.fiscal:
            impuesto = sum((l.impuesto_monto for l in lineas), CERO)
            cabecera.subtotal = total - impuesto
            cabecera.impuesto_total = impuesto
            cabecera.total = total
            cabecera.save(update_fields=["subtotal", "impuesto_total", "total"])
        else:
            cabecera.total = total
            cabecera.save(update_fields=["total"])

    @transaction.atomic
    def create(self, validated_data):
        lineas_data = validated_data.pop(self.campo_lineas, [])
        if self.tipo_secuencia:
            validated_data["numero"] = siguiente_numero(
                self._org(), self.tipo_secuencia, self.prefijo
            )
        cabecera = self.Meta.model.objects.create(**validated_data)
        self._crear_lineas(cabecera, lineas_data)
        self._recalcular_totales(cabecera)
        return cabecera

    @transaction.atomic
    def update(self, instance, validated_data):
        lineas_data = validated_data.pop(self.campo_lineas, None)
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        instance.save()
        if lineas_data is not None:
            getattr(instance, self.campo_lineas).all().delete()
            self._crear_lineas(instance, lineas_data)
        self._recalcular_totales(instance)
        return instance


# --------------------------------------------------------------------------- #
# Serializers de cabecera
# --------------------------------------------------------------------------- #
class CotizacionSerializer(_DocumentoConLineasMixin, serializers.ModelSerializer):
    modelo_linea = CotizacionDetalle
    campo_lineas = "detalles"
    campo_fk = "cotizacion"
    fiscal = True
    tipo_secuencia = "cotizacion"
    prefijo = "COT"

    detalles = CotizacionDetalleSerializer(many=True, required=False)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Cotizacion
        fields = [
            "id", "numero", "cliente", "cliente_nombre",
            "estado", "estado_display", "validez_dias", "notas",
            "subtotal", "impuesto_total", "total",
            "detalles", "creado_en", "actualizado_en",
        ]
        read_only_fields = [
            "numero", "subtotal", "impuesto_total", "total",
            "creado_en", "actualizado_en",
        ]


class VentaSerializer(_DocumentoConLineasMixin, serializers.ModelSerializer):
    modelo_linea = VentaDetalle
    campo_lineas = "detalles"
    campo_fk = "venta"
    fiscal = True
    tipo_secuencia = "venta"
    prefijo = "V"

    detalles = VentaDetalleSerializer(many=True, required=False)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    estado_pago_display = serializers.CharField(source="get_estado_pago_display", read_only=True)
    # Nota pública por QR: el panel muestra el QR y comparte el link con el cliente.
    url_publica = serializers.SerializerMethodField()
    url_qr = serializers.SerializerMethodField()

    class Meta:
        model = Venta
        fields = [
            "id", "numero", "cliente", "cliente_nombre",
            "estado", "estado_display", "estado_pago", "estado_pago_display",
            "cotizacion_origen", "notas",
            "subtotal", "impuesto_total", "total",
            "token_publico", "url_publica", "url_qr",
            "detalles", "creado_en", "actualizado_en",
        ]
        read_only_fields = [
            "numero", "subtotal", "impuesto_total", "total",
            "token_publico", "creado_en", "actualizado_en",
        ]

    def get_url_publica(self, obj):
        # Import local: publico.py importa este módulo (evita el ciclo).
        from .publico import url_nota_publica

        return url_nota_publica(obj, self.context.get("request"))

    def get_url_qr(self, obj):
        from django.urls import reverse

        ruta = reverse("nota-publica-qr", kwargs={"token": obj.token_publico})
        request = self.context.get("request")
        return request.build_absolute_uri(ruta) if request else ruta


class NotaPublicaDetalleSerializer(serializers.ModelSerializer):
    """Línea tal como la ve el cliente: qué se llevó y cuánto pagó."""

    class Meta:
        model = VentaDetalle
        fields = ["descripcion", "detalle", "cantidad", "precio_unitario", "total"]
        read_only_fields = fields


class NotaPublicaSerializer(serializers.ModelSerializer):
    """La nota de venta como la ve el cliente al escanear el QR.

    Es de **solo lectura y pública**: expone únicamente lo que ya está en el papel
    que se le entrega (negocio, número, fecha, líneas y totales). Nada de costos,
    márgenes, stock ni referencias internas."""

    negocio = serializers.CharField(source="organizacion.nombre", read_only=True)
    negocio_slug = serializers.CharField(source="organizacion.slug", read_only=True)
    cliente_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    estado_pago_display = serializers.CharField(source="get_estado_pago_display", read_only=True)
    fecha = serializers.DateTimeField(source="creado_en", read_only=True)
    detalles = NotaPublicaDetalleSerializer(many=True, read_only=True)

    class Meta:
        model = Venta
        fields = [
            "negocio", "negocio_slug", "numero", "fecha",
            "cliente_nombre", "estado", "estado_display",
            "estado_pago", "estado_pago_display", "notas",
            "subtotal", "impuesto_total", "total", "detalles",
        ]
        read_only_fields = fields

    def get_cliente_nombre(self, obj):
        if obj.cliente_id:
            return obj.cliente.nombre
        return obj.cliente_nombre or "Consumidor final"


class ListaSerializer(_DocumentoConLineasMixin, serializers.ModelSerializer):
    modelo_linea = ListaItem
    campo_lineas = "items"
    campo_fk = "lista"
    fiscal = False
    tipo_secuencia = None

    items = ListaItemSerializer(many=True, required=False)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Lista
        fields = [
            "id", "titulo", "cliente", "cliente_nombre",
            "estado", "estado_display", "notas", "total",
            "items", "creado_en", "actualizado_en",
        ]
        read_only_fields = ["total", "creado_en", "actualizado_en"]
