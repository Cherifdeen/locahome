from django.urls import path

from .views import AccueilView, MaisonPubliqueDetailView

app_name = "vitrine"

urlpatterns = [
    path("", AccueilView.as_view(), name="accueil"),
    path("offres/<int:pk>/", MaisonPubliqueDetailView.as_view(), name="maison_detail"),
]
