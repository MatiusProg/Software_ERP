"""
Estado de "organización activa" por request, guardado en un thread-local.

El middleware lo setea al inicio de cada request y lo limpia al final. Los
managers de los modelos multi-tenant lo leen para filtrar automáticamente,
de modo que ningún query cruce datos entre tenants por olvido.
"""

import threading

_state = threading.local()


def set_current_organization(organization):
    _state.organization = organization


def get_current_organization():
    return getattr(_state, "organization", None)


def clear_current_organization():
    if hasattr(_state, "organization"):
        del _state.organization
