from django.urls import path

from .views import (
    ConfirmerSortieView,
    MensuelPDFView,
    PaiementEntreeAvecLocataireView,
    PaiementEntreeCreateView,
    PaiementListView,
    PaiementMensuelCreateView,
    PaiementSortieView,
    PremierMoisEntreeView,
    SortiePDFView,
)

app_name = "paiements"

urlpatterns = [
    path("", PaiementListView.as_view(), name="liste"),
    path("entree/<int:chambre_id>/", PaiementEntreeAvecLocataireView.as_view(), name="entree_avec_locataire"),
    path("entree/", PaiementEntreeCreateView.as_view(), name="entree"),
    path("entree/<int:locataire_id>/premier-mois/", PremierMoisEntreeView.as_view(), name="premier_mois_entree"),
    path("mensuel/", PaiementMensuelCreateView.as_view(), name="mensuel"),
    path("mensuel/<int:paiement_id>/pdf/", MensuelPDFView.as_view(), name="mensuel_pdf"),
    path("sortie/", PaiementSortieView.as_view(), name="sortie"),
    path("sortie/<int:locataire_id>/", PaiementSortieView.as_view(), name="sortie_locataire"),
    path("sortie/confirmer/", ConfirmerSortieView.as_view(), name="sortie_confirmer"),
    path("sortie/<int:locataire_id>/pdf/", SortiePDFView.as_view(), name="sortie_pdf"),
]

