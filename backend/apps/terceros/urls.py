from rest_framework.routers import DefaultRouter

from .views import TerceroViewSet

router = DefaultRouter()
router.register("terceros", TerceroViewSet, basename="tercero")

urlpatterns = router.urls
