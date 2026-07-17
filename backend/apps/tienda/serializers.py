"""
Serializers públicos del escaparate.

Exponen SOLO campos aptos para un visitante anónimo. En particular NO se muestran
los precios internos (`precio_compra`, `precio_compra_maximo`, `precio_venta_minimo`
—el piso de negociación—) ni el `stock`.
"""

from rest_framework import serializers

from apps.catalogo.models import Categoria, Producto
from apps.cuentas.models import Organizacion


class TiendaOrganizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizacion
        fields = ["nombre", "slug"]


class TiendaCategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["id", "nombre", "descripcion"]


class TiendaProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)

    class Meta:
        model = Producto
        # Precio de venta público; sin costos, sin mínimo de negociación, sin stock.
        fields = [
            "id", "sku", "codigo_barras", "nombre",
            "categoria", "categoria_nombre", "unidad", "es_servicio",
            "precio_venta", "impuesto",
        ]
