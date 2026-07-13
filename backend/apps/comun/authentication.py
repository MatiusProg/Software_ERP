"""
Autenticación JWT que, además de identificar al usuario, fija la organización
activa y el usuario actual en el thread-local (para tenancy y auditoría).

La autenticación de DRF corre dentro de la vista (no en el middleware de
Django), así que este es el punto correcto para resolver el tenant en la API.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication

from .organizations import resolver_organizacion
from .tenancy import set_organizacion_actual, set_usuario_actual


class TenantJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            usuario, _token = result
            org = resolver_organizacion(usuario, request.headers.get("X-Organization"))
            set_organizacion_actual(org)
            set_usuario_actual(usuario)
            request._request.organizacion = org
        return result
