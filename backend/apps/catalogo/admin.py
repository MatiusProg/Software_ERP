from django.contrib import admin

from .models import Categoria, HistorialPrecio, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "organizacion", "creado_en")
    list_filter = ("organizacion",)
    search_fields = ("nombre",)
    autocomplete_fields = ("organizacion",)


class HistorialPrecioInline(admin.TabularInline):
    model = HistorialPrecio
    extra = 0
    can_delete = False
    readonly_fields = ("tipo", "valor", "usuario", "creado_en")
    fields = ("tipo", "valor", "usuario", "creado_en")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "sku", "nombre", "categoria", "unidad",
        "precio_venta", "stock", "activo", "organizacion",
    )
    list_filter = ("organizacion", "activo", "es_servicio", "unidad", "categoria")
    search_fields = ("sku", "codigo_barras", "nombre")
    autocomplete_fields = ("organizacion", "categoria")
    inlines = [HistorialPrecioInline]


@admin.register(HistorialPrecio)
class HistorialPrecioAdmin(admin.ModelAdmin):
    list_display = ("producto", "tipo", "valor", "usuario", "creado_en")
    list_filter = ("tipo", "organizacion")
    search_fields = ("producto__sku", "producto__nombre")
