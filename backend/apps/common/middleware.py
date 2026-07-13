"""
Middleware de tenancy.

- Para peticiones con sesión (ej. admin de Django) resuelve la organización
  desde ``request.user``.
- Para la API (JWT) la resolución real la hace ``TenantJWTAuthentication``
  dentro de la vista; aquí solo dejamos un valor por defecto.
- En ambos casos, garantiza que el thread-local se limpie al terminar el
  request (evita fugas entre peticiones que reusan el mismo hilo).
"""

from .organizations import resolve_organization
from .tenancy import set_current_organization, clear_current_organization


class CurrentOrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        org = resolve_organization(
            getattr(request, "user", None),
            request.headers.get("X-Organization"),
        )
        request.organization = org
        set_current_organization(org)
        try:
            response = self.get_response(request)
        finally:
            clear_current_organization()
        return response
