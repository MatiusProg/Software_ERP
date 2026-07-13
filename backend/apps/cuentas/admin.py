from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Membresia, Organizacion, Usuario


@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "activa", "creado_en")
    search_fields = ("nombre", "slug")
    prepopulated_fields = {"slug": ("nombre",)}


class MembresiaInline(admin.TabularInline):
    model = Membresia
    extra = 0
    autocomplete_fields = ("organizacion",)


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "nombre_completo", "is_staff", "is_active")
    search_fields = ("email", "nombre_completo")
    inlines = [MembresiaInline]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Datos", {"fields": ("nombre_completo",)}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "nombre_completo", "password1", "password2"),
        }),
    )


@admin.register(Membresia)
class MembresiaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "organizacion", "rol")
    list_filter = ("rol",)
    search_fields = ("usuario__email", "organizacion__nombre")
    autocomplete_fields = ("usuario", "organizacion")
