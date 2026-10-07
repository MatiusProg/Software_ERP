from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.comun.salud import salud
from apps.cuentas.views import LoginView

urlpatterns = [
    # Sonda de salud (healthcheck de Railway)
    path("salud/", salud, name="salud"),
    path("admin/", admin.site.urls),
    # Auth por JWT (login auditado)
    path("api/auth/token/", LoginView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Cuentas (registro, perfil)
    path("api/", include("apps.cuentas.urls")),
    # Catálogo (categorías, productos) y terceros (clientes/proveedores/transportadoras)
    path("api/", include("apps.catalogo.urls")),
    path("api/", include("apps.terceros.urls")),
    # Ventas, cotizaciones y listas (Fase 3)
    path("api/", include("apps.ventas.urls")),
    # Escaparate público (catálogo por slug, sin login)
    path("api/", include("apps.tienda.urls")),
    # Nota de venta pública por QR: /nota/<token>/ (página para el cliente)
    path("", include("apps.ventas.urls_publicas")),
]
