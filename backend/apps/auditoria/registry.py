"""
Registro de modelos a auditar. ``auditar(Modelo)`` conecta las señales que
generan automáticamente la bitácora en cada crear/actualizar/eliminar.
"""

from django.db.models.signals import pre_save, post_save, post_delete

from .models import Bitacora
from .servicios import crear_bitacora, valor_str, CAMPOS_EXCLUIDOS

MODELOS_AUDITADOS = set()


def _campos_auditables(sender):
    for field in sender._meta.concrete_fields:
        if field.primary_key:
            continue
        if field.name in CAMPOS_EXCLUIDOS:
            continue
        if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
            continue
        yield field


def _pre_save(sender, instance, **kwargs):
    """Guarda el estado anterior para poder comparar en post_save."""
    if not instance.pk:
        instance._auditoria_anterior = None
        return
    instance._auditoria_anterior = sender._base_manager.filter(pk=instance.pk).first()


def _post_save(sender, instance, created, **kwargs):
    if created:
        detalles = [
            {"campo": f.name, "valor_anterior": None,
             "valor_nuevo": valor_str(f.value_from_object(instance))}
            for f in _campos_auditables(sender)
        ]
        crear_bitacora(Bitacora.Accion.CREAR, instance=instance, detalles=detalles)
        return

    anterior = getattr(instance, "_auditoria_anterior", None)
    detalles = []
    for f in _campos_auditables(sender):
        nuevo = f.value_from_object(instance)
        viejo = f.value_from_object(anterior) if anterior is not None else None
        if viejo != nuevo:
            detalles.append({
                "campo": f.name,
                "valor_anterior": valor_str(viejo),
                "valor_nuevo": valor_str(nuevo),
            })
    if detalles:  # solo registrar si algo cambió realmente
        crear_bitacora(Bitacora.Accion.ACTUALIZAR, instance=instance, detalles=detalles)


def _post_delete(sender, instance, **kwargs):
    crear_bitacora(Bitacora.Accion.ELIMINAR, instance=instance)


def auditar(modelo):
    """Activa la auditoría automática para un modelo."""
    if modelo in MODELOS_AUDITADOS:
        return
    MODELOS_AUDITADOS.add(modelo)
    uid = f"auditoria_{modelo._meta.label}"
    pre_save.connect(_pre_save, sender=modelo, dispatch_uid=uid + "_pre")
    post_save.connect(_post_save, sender=modelo, dispatch_uid=uid + "_post")
    post_delete.connect(_post_delete, sender=modelo, dispatch_uid=uid + "_del")
