"""
Resolución de la organización activa de un usuario. Usado por el middleware
(sesión, ej. admin) y por la autenticación JWT (API).
"""


def resolver_organizacion(usuario, solicitada_id=None):
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return None

    # Import perezoso para evitar dependencias circulares en el arranque.
    from apps.cuentas.models import Membresia

    membresias = Membresia.objects.filter(usuario=usuario).select_related("organizacion")

    if solicitada_id:
        m = membresias.filter(organizacion_id=solicitada_id).first()
        if m:
            return m.organizacion

    m = membresias.first()
    return m.organizacion if m else None
