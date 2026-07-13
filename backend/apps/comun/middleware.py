"""
Middleware de tenancy.

- Para peticiones con sesión (ej. admin de Django) resuelve la organización y el
  usuario desde ``request.user``.
- Para la API (JWT) la resolución real la hace ``TenantJWTAuthentication`` dentro
  de la vista; aquí solo se deja un valor por defecto.
- Garantiza que el thread-local se limpie al terminar el request.
"""

from .organizations import resolver_organizacion
from .tenancy import (
    set_organizacion_actual,
    set_usuario_actual,
    set_meta_request,
    limpiar_estado,
)


def _ip_cliente(request):
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class CurrentOrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = getattr(request, "user", None)
        org = resolver_organizacion(usuario, request.headers.get("X-Organization"))
        request.organizacion = org
        set_organizacion_actual(org)
        set_meta_request(
            ip=_ip_cliente(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        )
        if usuario is not None and getattr(usuario, "is_authenticated", False):
            set_usuario_actual(usuario)
        try:
            response = self.get_response(request)
        finally:
            limpiar_estado()
        return response
