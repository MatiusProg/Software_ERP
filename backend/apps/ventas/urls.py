from rest_framework.routers import DefaultRouter

from .views import CotizacionViewSet, VentaViewSet, ListaViewSet

router = DefaultRouter()
router.register("cotizaciones", CotizacionViewSet, basename="cotizacion")
router.register("ventas", VentaViewSet, basename="venta")
router.register("listas", ListaViewSet, basename="lista")

urlpatterns = router.urls
