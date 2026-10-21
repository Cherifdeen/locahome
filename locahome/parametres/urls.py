from django.urls import path

from .views import ParametresUpdateView

app_name = "parametres"

urlpatterns = [
    path("", ParametresUpdateView.as_view(), name="modifier"),
]
