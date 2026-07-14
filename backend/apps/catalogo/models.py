"""
Catálogo: categorías, productos e historial de precios.

- ``Categoria`` / ``Producto`` heredan de ``ModeloTenant`` (aislados por
  organización y auditados automáticamente).
- ``HistorialPrecio`` guarda cada cambio de precio de un producto. Se llena solo
  por señal (ver ``senales.py``); es una tabla de negocio (para reportes de
  precios), independiente de la bitácora de auditoría.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.comun.models import ModeloTenant


def errores_precios(precio_venta, precio_venta_minimo, precio_compra, precio_compra_maximo):
    """Valida la coherencia de los precios. Devuelve un dict {campo: mensaje}
    (vacío si todo está bien). Un máximo/mínimo en 0 se interpreta como "sin
    tope"."""
    errores = {}
    if (precio_venta is not None and precio_venta_minimo
            and precio_venta_minimo > precio_venta):
        errores["precio_venta_minimo"] = (
            "El precio de venta mínimo no puede superar el precio de venta."
        )
    if (precio_compra_maximo and precio_compra is not None
            and precio_compra > precio_compra_maximo):
        errores["precio_compra"] = (
            "El precio de compra no puede superar el precio de compra máximo."
        )
    return errores


class Categoria(ModeloTenant):
    nombre = models.CharField(max_length=120)
    descripcion = models.CharField("descripción", max_length=255, blank=True)

    class Meta:
        db_table = "categoria"
        ordering = ["nombre"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        constraints = [
            models.UniqueConstraint(
                fields=["organizacion", "nombre"],
                name="categoria_nombre_unico_por_org",
            )
        ]

    def __str__(self):
        return self.nombre


class Producto(ModeloTenant):
    class Unidad(models.TextChoices):
        UNIDAD = "unidad", "Unidad"
        KG = "kg", "Kilogramo"
        LIBRA = "libra", "Libra"
        ARROBA = "arroba", "Arroba"
        LITRO = "litro", "Litro"
        CAJA = "caja", "Caja"
        PAQUETE = "paquete", "Paquete"
        SERVICIO = "servicio", "Servicio"

    sku = models.CharField("SKU", max_length=50)
    codigo_barras = models.CharField("código de barras", max_length=50, blank=True)
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="categoría",
        null=True,
        blank=True,
    )
    unidad = models.CharField(max_length=20, choices=Unidad.choices, default=Unidad.UNIDAD)
    es_servicio = models.BooleanField("es servicio", default=False)

    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    precio_venta_minimo = models.DecimalField(
        "precio de venta mínimo", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    precio_compra = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    precio_compra_maximo = models.DecimalField(
        "precio de compra máximo", max_digits=12, decimal_places=2, default=Decimal("0")
    )

    stock = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    impuesto = models.DecimalField(
        "impuesto (%)", max_digits=5, decimal_places=2, default=Decimal("13"),
        help_text="Porcentaje de IVA. En Bolivia, 13% por defecto.",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "producto"
        ordering = ["nombre"]
        verbose_name = "producto"
        verbose_name_plural = "productos"
        constraints = [
            models.UniqueConstraint(
                fields=["organizacion", "sku"], name="producto_sku_unico_por_org"
            ),
            # El código de barras es opcional: solo se exige unicidad cuando existe.
            models.UniqueConstraint(
                fields=["organizacion", "codigo_barras"],
                condition=~models.Q(codigo_barras=""),
                name="producto_codigobarras_unico_por_org",
            ),
        ]
        indexes = [
            models.Index(fields=["organizacion", "codigo_barras"]),
        ]

    def __str__(self):
        return f"{self.sku} · {self.nombre}"

    def clean(self):
        errores = errores_precios(
            self.precio_venta, self.precio_venta_minimo,
            self.precio_compra, self.precio_compra_maximo,
        )
        if errores:
            raise ValidationError(errores)


class HistorialPrecio(ModeloTenant):
    """Un registro por cada cambio de precio de un producto. Se llena por señal."""

    class Tipo(models.TextChoices):
        VENTA = "venta", "Precio de venta"
        VENTA_MINIMO = "venta_minimo", "Precio de venta mínimo"
        COMPRA = "compra", "Precio de compra"
        COMPRA_MAXIMO = "compra_maximo", "Precio de compra máximo"

    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name="historial_precios"
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    usuario = models.ForeignKey(
        "cuentas.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        db_table = "historial_precio"
        ordering = ["-creado_en"]
        verbose_name = "historial de precio"
        verbose_name_plural = "historial de precios"
        indexes = [
            models.Index(fields=["producto", "tipo", "-creado_en"]),
        ]

    def __str__(self):
        return f"{self.producto_id} {self.tipo}={self.valor}"
