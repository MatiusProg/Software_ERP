from rest_framework import serializers

from .models import Categoria, HistorialPrecio, Producto, errores_precios


def _unico_en_tenant(serializer, modelo, campo, valor, mensaje):
    """Valida unicidad de ``campo`` dentro del tenant activo (``objects`` ya está
    scopeado a la organización del request). Reemplaza al UniqueTogetherValidator
    de DRF, que no puede generarse porque ``organizacion`` no es campo expuesto."""
    qs = modelo.objects.filter(**{campo: valor})
    if serializer.instance is not None:
        qs = qs.exclude(pk=serializer.instance.pk)
    if qs.exists():
        raise serializers.ValidationError(mensaje)
    return valor


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["id", "nombre", "descripcion", "creado_en", "actualizado_en"]
        read_only_fields = ["creado_en", "actualizado_en"]

    def validate_nombre(self, value):
        return _unico_en_tenant(self, Categoria, "nombre", value,
                                "Ya existe una categoría con ese nombre.")


class HistorialPrecioSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = HistorialPrecio
        fields = ["id", "tipo", "tipo_display", "valor", "usuario", "creado_en"]
        read_only_fields = fields


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id", "sku", "codigo_barras", "nombre",
            "categoria", "categoria_nombre", "unidad", "es_servicio",
            "precio_venta", "precio_venta_minimo",
            "precio_compra", "precio_compra_maximo",
            "stock", "impuesto", "activo",
            "creado_en", "actualizado_en",
        ]
        read_only_fields = ["creado_en", "actualizado_en"]

    def validate_sku(self, value):
        return _unico_en_tenant(self, Producto, "sku", value,
                                "Ya existe un producto con ese SKU.")

    def validate_codigo_barras(self, value):
        if not value:
            return value
        return _unico_en_tenant(self, Producto, "codigo_barras", value,
                                "Ya existe un producto con ese código de barras.")

    def validate(self, attrs):
        # En un PATCH parcial, los campos ausentes se toman de la instancia.
        def valor(campo):
            if campo in attrs:
                return attrs[campo]
            return getattr(self.instance, campo, None)

        errores = errores_precios(
            valor("precio_venta"), valor("precio_venta_minimo"),
            valor("precio_compra"), valor("precio_compra_maximo"),
        )
        if errores:
            raise serializers.ValidationError(errores)
        return attrs
