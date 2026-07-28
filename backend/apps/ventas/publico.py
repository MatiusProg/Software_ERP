"""
Nota de venta pública por QR.

Idea: al emitir una venta, el sistema genera un **QR** que el cliente escanea con
la cámara del celular. El QR lleva a una página pública (sin login) con su nota,
desde donde puede **guardarla como imagen** en su galería, **mandarla por
WhatsApp** o **imprimirla / guardarla en PDF**.

Diseño y seguridad:

- El link no usa el id de la venta (secuencial, adivinable) sino
  ``Venta.token_publico``, un UUID4 aleatorio: quien tiene el link ve esa nota y
  ninguna otra. No hace falta login ni exponer la API privada.
- Son vistas públicas: ``AllowAny`` y sin JWT. Como no hay usuario, tampoco hay
  organización activa, así que se consulta con el manager ``todos`` (sin filtro
  implícito) — el aislamiento aquí lo da el token, igual que el ``slug`` en la
  app ``tienda``.
- Se muestra solo lo que el cliente ya tiene en su papel: número, fecha, líneas,
  totales y el negocio. Nunca costos, márgenes, stock ni datos de otras ventas.

El QR se genera en el servidor como **matriz de módulos** (``qrcode``) y se pinta
en SVG (endpoint ``qr.svg``, para el panel y la impresión) y en canvas (dentro de
la página, para la imagen que el cliente descarga). Así no dependemos de ningún
CDN ni de librerías JS externas.
"""

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import TemplateView
from rest_framework import generics
from rest_framework.permissions import AllowAny

import qrcode

from .models import Venta
from .serializers import NotaPublicaSerializer


# --------------------------------------------------------------------------- #
# Utilidades: URL pública y QR
# --------------------------------------------------------------------------- #
def url_nota_publica(venta, request=None):
    """URL absoluta de la nota pública de una venta.

    Usa ``NOTA_PUBLICA_BASE_URL`` si está configurada (útil cuando la API vive en
    un dominio y las notas se sirven en otro); si no, la arma con el host del
    request."""
    ruta = reverse("nota-publica", kwargs={"token": venta.token_publico})
    base = (settings.NOTA_PUBLICA_BASE_URL or "").rstrip("/")
    if base:
        return f"{base}{ruta}"
    if request is not None:
        return request.build_absolute_uri(ruta)
    return ruta


def matriz_qr(texto, borde=2):
    """Matriz de módulos del QR (lista de listas de booleanos).

    Se devuelve la matriz cruda —no una imagen— para poder pintarla igual en SVG
    (servidor) y en canvas (navegador) sin cargar archivos externos."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=borde,
    )
    qr.add_data(texto)
    qr.make(fit=True)
    return qr.get_matrix()


def svg_qr(texto, escala=8, borde=2):
    """QR en SVG (sin dependencias de imagen: no requiere Pillow)."""
    matriz = matriz_qr(texto, borde=borde)
    lado = len(matriz) * escala
    cuadros = "".join(
        f'<rect x="{x * escala}" y="{y * escala}" width="{escala}" height="{escala}"/>'
        for y, fila in enumerate(matriz)
        for x, modulo in enumerate(fila)
        if modulo
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{lado}" height="{lado}" '
        f'viewBox="0 0 {lado} {lado}" shape-rendering="crispEdges">'
        f'<rect width="{lado}" height="{lado}" fill="#ffffff"/>'
        f'<g fill="#000000">{cuadros}</g></svg>'
    )


def _venta_por_token(token):
    """Venta buscada por su token público (sin filtro de tenant: no hay usuario)."""
    return get_object_or_404(
        Venta.todos.select_related("organizacion", "cliente").prefetch_related("detalles"),
        token_publico=token,
    )


# --------------------------------------------------------------------------- #
# Vistas públicas
# --------------------------------------------------------------------------- #
class NotaPublicaJSONView(generics.RetrieveAPIView):
    """``GET /api/nota/<token>/`` — la nota en JSON (para la PWA o integraciones)."""

    authentication_classes = []       # público: sin JWT
    permission_classes = [AllowAny]
    serializer_class = NotaPublicaSerializer

    def get_object(self):
        return _venta_por_token(self.kwargs["token"])


class NotaPublicaPaginaView(TemplateView):
    """``GET /nota/<token>/`` — la página que abre el cliente al escanear el QR."""

    template_name = "ventas/nota_publica.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        venta = _venta_por_token(self.kwargs["token"])
        url = url_nota_publica(venta, self.request)
        contexto["venta"] = venta
        contexto["nota"] = NotaPublicaSerializer(venta).data
        contexto["url_publica"] = url
        contexto["qr"] = matriz_qr(url)
        return contexto


def nota_publica_qr_svg(request, token):
    """``GET /nota/<token>/qr.svg`` — el QR solo, para mostrarlo o imprimirlo."""
    venta = _venta_por_token(token)
    svg = svg_qr(url_nota_publica(venta, request))
    respuesta = HttpResponse(svg, content_type="image/svg+xml")
    # El QR de una venta nunca cambia: se puede cachear con tranquilidad.
    respuesta["Cache-Control"] = "public, max-age=86400"
    return respuesta
