from django.contrib import admin

from .models import ContactoTercero, Tercero, UbicacionTercero


class ContactoTerceroInline(admin.TabularInline):
    model = ContactoTercero
    extra = 0
    exclude = ("organizacion",)  # se hereda del tercero (ver save_formset)


class UbicacionTerceroInline(admin.TabularInline):
    model = UbicacionTercero
    extra = 0
    exclude = ("organizacion",)


@admin.register(Tercero)
class TerceroAdmin(admin.ModelAdmin):
    list_display = (
        "nombre", "nit_ci",
        "es_cliente", "es_proveedor", "es_transportadora",
        "activo", "organizacion",
    )
    list_filter = (
        "organizacion", "es_cliente", "es_proveedor", "es_transportadora", "activo",
    )
    search_fields = ("nombre", "nit_ci")
    autocomplete_fields = ("organizacion",)
    inlines = [ContactoTerceroInline, UbicacionTerceroInline]

    def save_formset(self, request, form, formset, change):
        """Los contactos/ubicaciones heredan la organización del tercero."""
        instancias = formset.save(commit=False)
        for obj in instancias:
            if isinstance(obj, (ContactoTercero, UbicacionTercero)):
                obj.organizacion = form.instance.organizacion
            obj.save()
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()
