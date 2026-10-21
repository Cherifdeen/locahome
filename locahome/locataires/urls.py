from django.urls import path

from .views import (
    FormalitesEntreeView,
    FormalitesPDFView,
    LocataireDetailView,
    LocataireListView,
    LocataireUpdateView,
    PremierMoisPDFView,
    PremierMoisView,
)

app_name = "locataires"

urlpatterns = [
    path("", LocataireListView.as_view(), name="liste"),
    path("<int:pk>/", LocataireDetailView.as_view(), name="detail"),
    path("<int:pk>/modifier/", LocataireUpdateView.as_view(), name="modifier"),
    # Processus d'entrée en 2 étapes
    path("chambre/<int:chambre_id>/formalites/", FormalitesEntreeView.as_view(), name="formalites_entree"),
    path("<int:locataire_id>/premier-mois/", PremierMoisView.as_view(), name="premier_mois"),
    # PDF
    path("<int:locataire_id>/pdf/formalites/", FormalitesPDFView.as_view(), name="pdf_formalites"),
    path("<int:locataire_id>/pdf/premier-mois/", PremierMoisPDFView.as_view(), name="pdf_premier_mois"),
]


