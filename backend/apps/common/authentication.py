"""
Autenticación JWT que, además de identificar al usuario, fija la organización
activa en el thread-local del tenant.

La autenticación de DRF corre dentro de la vista (no en el middleware de
Django), así que este es el punto correcto para resolver el tenant en peticiones
de la API.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication

from .organizations import resolve_organization
from .tenancy import set_current_organization


class TenantJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user, _token = result
            org = resolve_organization(user, request.headers.get("X-Organization"))
            set_current_organization(org)
            # Deja la org accesible como request.organization en la vista.
            request._request.organization = org
        return result
