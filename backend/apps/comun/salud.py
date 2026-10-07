"""
Sonda de salud: ``GET /salud/``.

La usa el healthcheck de Railway antes de dar por bueno un despliegue, y sirve
para comprobar a mano que la API responde. Contesta 200 solo si además la base
de datos responde: una API arriba sin base no está sana.

Está exenta de la redirección a HTTPS (``SECURE_REDIRECT_EXEMPT`` en settings)
porque Railway la llama por HTTP interno; un 301 lo tomaría como fallo. No
expone nada: ni versión, ni datos, ni detalles del error.
"""

from django.db import connection
from django.http import JsonResponse


def salud(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"estado": "sin base de datos"}, status=503)
    return JsonResponse({"estado": "ok"})
