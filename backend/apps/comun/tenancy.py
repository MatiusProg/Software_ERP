"""
Estado por-request guardado en un thread-local: organización activa, usuario
actual, IP y user-agent. El middleware/autenticación lo setean al inicio de cada
request y lo limpian al final.

- La organización activa la usan los managers multi-tenant para filtrar.
- El usuario actual, IP y user-agent los usa la auditoría.
"""

import threading

_state = threading.local()


# --- Organización activa -----------------------------------------------------
def set_organizacion_actual(organizacion):
    _state.organizacion = organizacion


def get_organizacion_actual():
    return getattr(_state, "organizacion", None)


# --- Usuario actual ----------------------------------------------------------
def set_usuario_actual(usuario):
    _state.usuario = usuario


def get_usuario_actual():
    return getattr(_state, "usuario", None)


# --- Metadatos del request (para auditoría) ----------------------------------
def set_meta_request(ip=None, user_agent=None):
    _state.ip = ip
    _state.user_agent = user_agent


def get_ip_actual():
    return getattr(_state, "ip", None)


def get_user_agent_actual():
    return getattr(_state, "user_agent", None)


def limpiar_estado():
    for attr in ("organizacion", "usuario", "ip", "user_agent"):
        if hasattr(_state, attr):
            delattr(_state, attr)
