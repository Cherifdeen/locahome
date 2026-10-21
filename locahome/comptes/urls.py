from django.urls import path

from .views import InscriptionView

app_name = "comptes"

urlpatterns = [
    path("inscription/", InscriptionView.as_view(), name="inscription"),
]
