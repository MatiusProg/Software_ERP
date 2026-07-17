from django.urls import path

from .views import TiendaInfoView, TiendaCategoriasView, TiendaProductosView

urlpatterns = [
    path("tienda/<slug:slug>/", TiendaInfoView.as_view(), name="tienda-info"),
    path("tienda/<slug:slug>/categorias/", TiendaCategoriasView.as_view(), name="tienda-categorias"),
    path("tienda/<slug:slug>/productos/", TiendaProductosView.as_view(), name="tienda-productos"),
]
