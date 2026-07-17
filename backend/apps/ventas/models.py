"""
Ventas, cotizaciones y listas (Fase 3).

Tres documentos con la misma estructura cabecera + detalle:

- ``Cotizacion`` / ``CotizacionDetalle``: propuesta de precios a un cliente.
- ``Venta`` / ``VentaDetalle``: nota de venta (no descuenta stock en esta fase; el
  inventario llega en la Fase 4).
- ``Lista`` / ``ListaItem``: listas de pendientes (el puente con la PWA); items
  informales que pueden marcarse como comprados.

Decisiones aplicadas (ver docs/PLAN.md y notas de Fase 3):
- **Precio congelado en la línea**: el detalle guarda su propio ``total`` (y, si
  aplica, ``precio_unitario``); cambiar el precio del producto no altera documentos
  ya emitidos.
- **Correlativos por organización**: V-0001, COT-0001… con contador por tenant
  (``SecuenciaDocumento``), no una secuencia global.
- **Doble modo de línea**: por defecto se escribe el ``total`` directo; de forma
  opcional se dan ``cantidad`` + ``precio_unitario`` y el total se calcula.
- **Cliente opcional**: FK a ``Tercero`` + ``cliente_nombre`` libre para venta de
  mostrador / consumidor final sin registrar.
- **Impuesto**: los precios se manejan **IVA incluido** (típico en retail boliviano);
  el impuesto contenido se discrimina para el desglose. La tasa se congela por línea.
"""

from decimal import Decimal

from django.db import models, transaction

from apps.comun.models import ModeloTenant

CENTAVO = Decimal("0.01")


class SecuenciaDocumento(models.Model):
    """Contador correlativo por organización y tipo de documento.

    No es un ``ModeloTenant`` (es infraestructura interna, no se lista ni audita):
    solo un contador que se incrementa de forma atómica al emitir un documento.
    """

    organizacion = models.ForeignKey(
        "cuentas.Organizacion", on_delete=models.CASCADE, related_name="+"
    )
    tipo = models.CharField(max_length=20)  # 'venta', 'cotizacion'
    valor = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "secuencia_documento"
        constraints = [
            models.UniqueConstraint(
                fields=["organizacion", "tipo"], name="secuencia_unica_por_org_tipo"
            )
        ]

    def __str__(self):
        return f"{self.organizacion_id} {self.tipo}={self.valor}"


def siguiente_numero(organizacion, tipo, prefijo):
    """Devuelve el próximo número correlativo (ej. ``V-0001``) para el tenant.

    Debe llamarse dentro de una transacción; usa ``select_for_update`` para que
    dos ventas simultáneas no obtengan el mismo número."""
    seq, _ = SecuenciaDocumento.objects.select_for_update().get_or_create(
        organizacion=organizacion, tipo=tipo
    )
    seq.valor += 1
    seq.save(update_fields=["valor"])
    return f"{prefijo}-{seq.valor:04d}"


class LineaDocumento(ModeloTenant):
    """Línea de detalle compartida por los tres documentos.

    Dos modos de captura:
    - **Directo** (por defecto): se escribe ``total``; ``cantidad`` y
      ``precio_unitario`` quedan en null.
    - **Unitario** (opt-in): se dan ``cantidad`` y ``precio_unitario``; el ``total``
      pasa a calcularse (cantidad × precio_unitario).

    ``producto`` es opcional: las listas/cotizaciones que vienen de la PWA usan
    texto libre en ``descripcion`` sin un producto del catálogo detrás.
    """

    producto = models.ForeignKey(
        "catalogo.Producto",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    descripcion = models.CharField("descripción", max_length=255)
    detalle = models.CharField(
        max_length=255, blank=True,
        help_text="Empaque o nota libre, ej. '1 java', '6 cajas', '1/4'.",
    )
    cantidad = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True
    )
    precio_unitario = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["orden", "id"]

    @property
    def es_modo_unitario(self):
        return self.cantidad is not None and self.precio_unitario is not None

    def calcular_total(self):
        """Total de la línea: calculado si está en modo unitario, si no el ``total``
        ingresado directo."""
        if self.es_modo_unitario:
            return (self.cantidad * self.precio_unitario).quantize(CENTAVO)
        return self.total or Decimal("0")


class LineaFiscal(LineaDocumento):
    """Línea con impuesto congelado (cotización y venta). Los precios son IVA
    incluido; ``impuesto_monto`` discrimina el impuesto contenido en el total."""

    impuesto = models.DecimalField(
        "impuesto (%)", max_digits=5, decimal_places=2, default=Decimal("13")
    )

    class Meta(LineaDocumento.Meta):
        abstract = True

    @property
    def impuesto_monto(self):
        imp = self.impuesto or Decimal("0")
        total = self.calcular_total()
        if not imp:
            return Decimal("0.00")
        return (total * imp / (Decimal("100") + imp)).quantize(CENTAVO)


# --------------------------------------------------------------------------- #
# Cotización
# --------------------------------------------------------------------------- #
class Cotizacion(ModeloTenant):
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        ENVIADA = "enviada", "Enviada"
        ACEPTADA = "aceptada", "Aceptada"
        RECHAZADA = "rechazada", "Rechazada"
        VENCIDA = "vencida", "Vencida"

    numero = models.CharField(max_length=20, blank=True)
    cliente = models.ForeignKey(
        "terceros.Tercero", on_delete=models.PROTECT, null=True, blank=True,
        related_name="cotizaciones",
    )
    cliente_nombre = models.CharField("nombre del cliente", max_length=200, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.BORRADOR)
    validez_dias = models.PositiveIntegerField("validez (días)", default=15)
    notas = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    impuesto_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))

    class Meta:
        db_table = "cotizacion"
        ordering = ["-creado_en"]
        verbose_name = "cotización"
        verbose_name_plural = "cotizaciones"
        constraints = [
            models.UniqueConstraint(
                fields=["organizacion", "numero"], name="cotizacion_numero_unico_por_org"
            )
        ]

    def __str__(self):
        return self.numero or f"COT s/n ({self.pk})"


class CotizacionDetalle(LineaFiscal):
    cotizacion = models.ForeignKey(
        Cotizacion, on_delete=models.CASCADE, related_name="detalles"
    )

    class Meta(LineaFiscal.Meta):
        db_table = "cotizacion_detalle"
        verbose_name = "detalle de cotización"
        verbose_name_plural = "detalles de cotización"


# --------------------------------------------------------------------------- #
# Venta
# --------------------------------------------------------------------------- #
class Venta(ModeloTenant):
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        CONFIRMADA = "confirmada", "Confirmada"
        ANULADA = "anulada", "Anulada"

    class EstadoPago(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        PARCIAL = "parcial", "Parcial"
        PAGADO = "pagado", "Pagado"

    numero = models.CharField(max_length=20, blank=True)
    cliente = models.ForeignKey(
        "terceros.Tercero", on_delete=models.PROTECT, null=True, blank=True,
        related_name="ventas",
    )
    cliente_nombre = models.CharField("nombre del cliente", max_length=200, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.CONFIRMADA)
    estado_pago = models.CharField(
        "estado de pago", max_length=20, choices=EstadoPago.choices, default=EstadoPago.PENDIENTE
    )
    cotizacion_origen = models.ForeignKey(
        Cotizacion, on_delete=models.SET_NULL, null=True, blank=True, related_name="ventas",
    )
    notas = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    impuesto_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))

    class Meta:
        db_table = "venta"
        ordering = ["-creado_en"]
        verbose_name = "venta"
        verbose_name_plural = "ventas"
        constraints = [
            models.UniqueConstraint(
                fields=["organizacion", "numero"], name="venta_numero_unico_por_org"
            )
        ]

    def __str__(self):
        return self.numero or f"V s/n ({self.pk})"


class VentaDetalle(LineaFiscal):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")

    class Meta(LineaFiscal.Meta):
        db_table = "venta_detalle"
        verbose_name = "detalle de venta"
        verbose_name_plural = "detalles de venta"


# --------------------------------------------------------------------------- #
# Lista de pendientes (puente con la PWA)
# --------------------------------------------------------------------------- #
class Lista(ModeloTenant):
    class Estado(models.TextChoices):
        ABIERTA = "abierta", "Abierta"
        CERRADA = "cerrada", "Cerrada"

    titulo = models.CharField("título", max_length=200)
    cliente = models.ForeignKey(
        "terceros.Tercero", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="listas",
    )
    cliente_nombre = models.CharField("nombre del cliente", max_length=200, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ABIERTA)
    notas = models.TextField(blank=True)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))

    class Meta:
        db_table = "lista"
        ordering = ["-creado_en"]
        verbose_name = "lista"
        verbose_name_plural = "listas"

    def __str__(self):
        return self.titulo


class ListaItem(LineaDocumento):
    """Item de lista: sin impuesto (informal), con marca de comprado (la PWA
    tacha lo ya comprado)."""

    lista = models.ForeignKey(Lista, on_delete=models.CASCADE, related_name="items")
    comprado = models.BooleanField(default=False)

    class Meta(LineaDocumento.Meta):
        db_table = "lista_item"
        verbose_name = "item de lista"
        verbose_name_plural = "items de lista"
