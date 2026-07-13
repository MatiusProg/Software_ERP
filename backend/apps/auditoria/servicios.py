"""
Servicios de auditoría: crean registros de ``Bitacora`` (+ detalles) de forma
segura. Si algo falla al auditar, NUNCA debe romper la operación de negocio.
"""

import logging

from apps.comun.tenancy import (
    get_usuario_actual,
    get_organizacion_actual,
    get_ip_actual,
    get_user_agent_actual,
)

logger = logging.getLogger("auditoria")

# Campos que nunca se auditan (sensibles o ruido).
CAMPOS_EXCLUIDOS = {"password", "last_login", "creado_en", "actualizado_en"}


def valor_str(valor):
    return None if valor is None else str(valor)


def _organizacion_de(instance):
    """Deduce la organización a la que pertenece el objeto auditado."""
    from apps.cuentas.models import Organizacion

    if isinstance(instance, Organizacion):
        return instance
    if hasattr(instance, "organizacion_id") and instance.organizacion_id:
        return instance.organizacion
    return get_organizacion_actual()


def crear_bitacora(accion, instance=None, usuario=None, organizacion=None,
                   descripcion="", detalles=None):
    """Crea una entrada de bitácora + sus detalles. Tolerante a fallos."""
    from .models import Bitacora, BitacoraDetalle

    try:
        if usuario is None:
            usuario = get_usuario_actual()
        if organizacion is None and instance is not None:
            organizacion = _organizacion_de(instance)
        if organizacion is None:
            organizacion = get_organizacion_actual()

        bitacora = Bitacora.objects.create(
            organizacion=organizacion,
            usuario=usuario,
            accion=accion,
            modelo=instance._meta.label if instance is not None else "",
            objeto_id=str(instance.pk) if getattr(instance, "pk", None) else "",
            objeto_desc=(str(instance)[:255] if instance is not None else ""),
            descripcion=descripcion or "",
            ip=get_ip_actual(),
            user_agent=get_user_agent_actual() or "",
        )
        if detalles:
            BitacoraDetalle.objects.bulk_create([
                BitacoraDetalle(
                    bitacora=bitacora,
                    campo=d["campo"],
                    valor_anterior=d.get("valor_anterior"),
                    valor_nuevo=d.get("valor_nuevo"),
                )
                for d in detalles
            ])
        return bitacora
    except Exception:  # noqa: BLE001 — auditar jamás debe romper el negocio
        logger.exception("No se pudo registrar la bitácora (accion=%s)", accion)
        return None
