from django.urls import path
from rest_framework.routers import DefaultRouter

from .publico import NotaPublicaJSONView
from .views import CotizacionViewSet, VentaViewSet, ListaViewSet

router = DefaultRouter()
router.register("cotizaciones", CotizacionViewSet, basename="cotizacion")
router.register("ventas", VentaViewSet, basename="venta")
router.register("listas", ListaViewSet, basename="lista")

urlpatterns = [
    # Nota pública en JSON (sin login, por token). La página para el cliente
    # vive en urls_publicas.py.
    path("nota/<uuid:token>/", NotaPublicaJSONView.as_view(), name="nota-publica-json"),
] + router.urls
