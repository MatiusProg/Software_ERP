"""
Señales del catálogo: llenan ``HistorialPrecio`` automáticamente cuando cambia
algún precio de un ``Producto``.

- Al crear: registra los precios iniciales que no sean cero.
- Al actualizar: registra solo los precios que efectivamente cambiaron.

El usuario que hizo el cambio se toma del thread-local (igual que la auditoría).
No debe romper el guardado del producto si algo falla al historiar.
"""

import logging

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from apps.comun.tenancy import get_usuario_actual
from .models import Producto, HistorialPrecio

logger = logging.getLogger("catalogo")

# Campo del producto -> tipo de historial.
PRECIO_A_TIPO = {
    "precio_venta": HistorialPrecio.Tipo.VENTA,
    "precio_venta_minimo": HistorialPrecio.Tipo.VENTA_MINIMO,
    "precio_compra": HistorialPrecio.Tipo.COMPRA,
    "precio_compra_maximo": HistorialPrecio.Tipo.COMPRA_MAXIMO,
}


@receiver(pre_save, sender=Producto, dispatch_uid="catalogo_historial_pre")
def _guardar_precios_anteriores(sender, instance, **kwargs):
    """Guarda el estado previo de los precios para comparar en post_save."""
    if not instance.pk:
        instance._precios_anteriores = None
        return
    instance._precios_anteriores = sender.todos.filter(pk=instance.pk).first()


@receiver(post_save, sender=Producto, dispatch_uid="catalogo_historial_post")
def _historiar_cambios_de_precio(sender, instance, created, **kwargs):
    try:
        anterior = getattr(instance, "_precios_anteriores", None)
        usuario = get_usuario_actual()
        registros = []
        for campo, tipo in PRECIO_A_TIPO.items():
            nuevo = getattr(instance, campo)
            if created:
                if nuevo:  # precio inicial distinto de cero
                    registros.append(_nuevo_registro(instance, tipo, nuevo, usuario))
            else:
                viejo = getattr(anterior, campo, None) if anterior else None
                if viejo != nuevo:
                    registros.append(_nuevo_registro(instance, tipo, nuevo, usuario))
        if registros:
            HistorialPrecio.objects.bulk_create(registros)
    except Exception:  # noqa: BLE001 — historiar jamás debe romper el guardado
        logger.exception("No se pudo registrar el historial de precios (producto=%s)",
                         getattr(instance, "pk", None))


def _nuevo_registro(producto, tipo, valor, usuario):
    # bulk_create no llama a save(), así que la organización se asigna a mano.
    return HistorialPrecio(
        organizacion=producto.organizacion,
        producto=producto,
        tipo=tipo,
        valor=valor,
        usuario=usuario,
    )
