from django.urls import path

from .views import RegistroView, YoView

urlpatterns = [
    path("registro/", RegistroView.as_view(), name="registro"),
    path("yo/", YoView.as_view(), name="yo"),
]
