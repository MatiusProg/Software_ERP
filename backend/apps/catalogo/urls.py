from rest_framework.routers import DefaultRouter

from .views import CategoriaViewSet, ProductoViewSet

router = DefaultRouter()
router.register("categorias", CategoriaViewSet, basename="categoria")
router.register("productos", ProductoViewSet, basename="producto")

urlpatterns = router.urls
