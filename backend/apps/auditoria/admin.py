from django.contrib import admin

from .models import Bitacora, BitacoraDetalle


class BitacoraDetalleInline(admin.TabularInline):
    model = BitacoraDetalle
    extra = 0
    can_delete = False
    readonly_fields = ("campo", "valor_anterior", "valor_nuevo")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Bitacora)
class BitacoraAdmin(admin.ModelAdmin):
    list_display = ("fecha", "accion", "modelo", "objeto_desc", "usuario", "organizacion")
    list_filter = ("accion", "modelo", "organizacion")
    search_fields = ("modelo", "objeto_id", "objeto_desc", "usuario__email", "descripcion")
    date_hierarchy = "fecha"
    inlines = [BitacoraDetalleInline]
    readonly_fields = (
        "organizacion", "usuario", "accion", "modelo", "objeto_id",
        "objeto_desc", "descripcion", "ip", "user_agent", "fecha",
    )

    # La bitácora es de solo lectura: nadie la crea/edita/borra a mano.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
