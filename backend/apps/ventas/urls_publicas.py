"""Rutas públicas de la nota de venta (fuera de ``/api/``: son para humanos).

Van en la raíz porque este link se imprime en un QR y viaja por WhatsApp: cuanto
más corto y legible, mejor (``/nota/<token>/``).
"""

from django.urls import path

from .publico import NotaPublicaPaginaView, nota_publica_qr_svg

urlpatterns = [
    path("nota/<uuid:token>/", NotaPublicaPaginaView.as_view(), name="nota-publica"),
    path("nota/<uuid:token>/qr.svg", nota_publica_qr_svg, name="nota-publica-qr"),
]
