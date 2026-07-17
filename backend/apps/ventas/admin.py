from django.contrib import admin

from .models import (
    Cotizacion, CotizacionDetalle,
    Venta, VentaDetalle,
    Lista, ListaItem,
)


class CotizacionDetalleInline(admin.TabularInline):
    model = CotizacionDetalle
    extra = 0


class VentaDetalleInline(admin.TabularInline):
    model = VentaDetalle
    extra = 0


class ListaItemInline(admin.TabularInline):
    model = ListaItem
    extra = 0


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ["numero", "cliente_nombre", "estado", "total", "creado_en"]
    list_filter = ["estado"]
    search_fields = ["numero", "cliente_nombre"]
    inlines = [CotizacionDetalleInline]


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ["numero", "cliente_nombre", "estado", "estado_pago", "total", "creado_en"]
    list_filter = ["estado", "estado_pago"]
    search_fields = ["numero", "cliente_nombre"]
    inlines = [VentaDetalleInline]


@admin.register(Lista)
class ListaAdmin(admin.ModelAdmin):
    list_display = ["titulo", "cliente_nombre", "estado", "total", "creado_en"]
    list_filter = ["estado"]
    search_fields = ["titulo", "cliente_nombre"]
    inlines = [ListaItemInline]
