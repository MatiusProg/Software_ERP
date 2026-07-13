"""
Permisos basados en el rol de la membresía del usuario en la organización activa.

Uso en una vista DRF:

    from apps.cuentas.permisos import TieneRol
    from apps.cuentas.models import Membresia

    class ProductoViewSet(...):
        permission_classes = [TieneRol(Membresia.Rol.PROPIETARIO,
                                       Membresia.Rol.ADMIN,
                                       Membresia.Rol.VENDEDOR)]
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


def rol_actual(request):
    """Devuelve el rol (str) del usuario en la organización activa, o None."""
    org = getattr(request, "organizacion", None)
    usuario = getattr(request, "user", None)
    if org is None or usuario is None or not usuario.is_authenticated:
        return None

    from .models import Membresia

    m = Membresia.objects.filter(usuario=usuario, organizacion=org).first()
    return m.rol if m else None


def TieneRol(*roles_permitidos):
    """Fábrica de permiso: exige que el rol activo esté entre los permitidos."""

    class PermisoRol(BasePermission):
        message = "No tienes el rol necesario para esta acción."

        def has_permission(self, request, view):
            return rol_actual(request) in roles_permitidos

    return PermisoRol


class SoloLecturaOAdmin(BasePermission):
    """Lectura para cualquier miembro; escritura solo propietario/admin."""

    message = "Solo propietario o administrador pueden modificar."

    def has_permission(self, request, view):
        rol = rol_actual(request)
        if rol is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return rol in ("propietario", "admin")
