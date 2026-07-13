"""
Resolución de la organización activa de un usuario.

Usado tanto por el middleware (sesión, ej. admin) como por la clase de
autenticación JWT de DRF (API). Centralizado aquí para no duplicar la lógica.
"""


def resolve_organization(user, requested_id=None):
    if user is None or not getattr(user, "is_authenticated", False):
        return None

    # Import perezoso: evita dependencias circulares en el arranque.
    from apps.accounts.models import Membership

    memberships = Membership.objects.filter(user=user).select_related("organization")

    if requested_id:
        m = memberships.filter(organization_id=requested_id).first()
        if m:
            return m.organization

    m = memberships.first()
    return m.organization if m else None
