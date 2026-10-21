from django.urls import path

from .views import (
    ChambreCreateView,
    ChambreDeleteView,
    ChambreDetailView,
    ChambreListView,
    ChambreUpdateView,
    ChambresLibresView,
)

app_name = "chambres"

urlpatterns = [
    path("", ChambreListView.as_view(), name="liste"),
    path("libres/", ChambresLibresView.as_view(), name="libres"),
    path("nouvelle/", ChambreCreateView.as_view(), name="creer"),
    path("<int:pk>/", ChambreDetailView.as_view(), name="detail"),
    path("<int:pk>/modifier/", ChambreUpdateView.as_view(), name="modifier"),
    path("<int:pk>/supprimer/", ChambreDeleteView.as_view(), name="supprimer"),
]



