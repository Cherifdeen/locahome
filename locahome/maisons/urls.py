from django.urls import path

from .views import (
    MaisonCreateView,
    MaisonDeleteView,
    MaisonDetailView,
    MaisonListView,
    MaisonUpdateView,
)

app_name = "maisons"

urlpatterns = [
    path("", MaisonListView.as_view(), name="liste"),
    path("ajouter/", MaisonCreateView.as_view(), name="ajouter"),
    path("<int:pk>/", MaisonDetailView.as_view(), name="detail"),
    path("<int:pk>/modifier/", MaisonUpdateView.as_view(), name="modifier"),
    path("<int:pk>/supprimer/", MaisonDeleteView.as_view(), name="supprimer"),
]
