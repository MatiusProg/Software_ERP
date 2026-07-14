from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.cuentas.views import LoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Auth por JWT (login auditado)
    path("api/auth/token/", LoginView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Cuentas (registro, perfil)
    path("api/", include("apps.cuentas.urls")),
    # Catálogo (categorías, productos) y terceros (clientes/proveedores/transportadoras)
    path("api/", include("apps.catalogo.urls")),
    path("api/", include("apps.terceros.urls")),
]
