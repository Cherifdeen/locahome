"""
Service de calcul des statistiques du dashboard propriétaire.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from django.db.models import Sum

if TYPE_CHECKING:
    from locahome.comptes.models import Proprietaire


@dataclass
class StatistiquesDashboard:
    """Statistiques globales pour le dashboard."""
    
    # Maisons
    nombre_maisons: int
    
    # Chambres
    chambres_total: int
    chambres_occupees: int
    chambres_libres: int
    taux_occupation: float
    
    # Revenus
    revenus_mois_courant: Decimal
    revenus_mois_precedent: Decimal
    evolution_revenus: float
    
    # Retards
    nb_locataires_en_retard: int
    locataires_en_retard: list
    
    # Alertes avance
    nb_alertes_avance: int
    alertes_avance: list
    
    # Problèmes
    nb_problemes_ouverts: int
    problemes_ouverts: list


def get_statistiques_dashboard(proprietaire: "Proprietaire") -> StatistiquesDashboard:
    """
    Calcule toutes les statistiques du dashboard pour un propriétaire.
    
    Args:
        proprietaire: Le propriétaire connecté
    
    Returns:
        StatistiquesDashboard avec toutes les données
    """
    from locahome.chambres.models import Chambre, NoteChambre
    from locahome.locataires.models import Locataire
    from locahome.maisons.models import Maison
    from locahome.paiements.models import Paiement
    from locahome.services.avance import get_avance_en_mois, get_niveau_alerte
    from locahome.services.paiements import get_mois_impayes
    
    # === MAISONS ===
    maisons = Maison.objects.filter(proprietaire=proprietaire)
    nombre_maisons = maisons.count()
    
    # === CHAMBRES ===
    chambres = Chambre.objects.filter(maison__proprietaire=proprietaire)
    chambres_total = chambres.count()
    chambres_occupees = chambres.filter(statut="OCCUPEE").count()
    chambres_libres = chambres.filter(statut="LIBRE").count()
    taux_occupation = (chambres_occupees / chambres_total * 100) if chambres_total > 0 else 0
    
    # === REVENUS ===
    aujourdhui = date.today()
    mois_courant = aujourdhui.month
    annee_courante = aujourdhui.year
    
    # Mois précédent
    if mois_courant == 1:
        mois_precedent = 12
        annee_precedente = annee_courante - 1
    else:
        mois_precedent = mois_courant - 1
        annee_precedente = annee_courante
    
    # Paiements du mois courant
    paiements_mois_courant = Paiement.objects.filter(
        locataire__chambre__maison__proprietaire=proprietaire,
        date_paiement__month=mois_courant,
        date_paiement__year=annee_courante,
    )
    revenus_mois_courant = paiements_mois_courant.aggregate(
        total=Sum("montant_paye")
    )["total"] or Decimal("0")
    
    # Paiements du mois précédent
    paiements_mois_precedent = Paiement.objects.filter(
        locataire__chambre__maison__proprietaire=proprietaire,
        date_paiement__month=mois_precedent,
        date_paiement__year=annee_precedente,
    )
    revenus_mois_precedent = paiements_mois_precedent.aggregate(
        total=Sum("montant_paye")
    )["total"] or Decimal("0")
    
    # Évolution
    if revenus_mois_precedent > 0:
        evolution_revenus = float(
            (revenus_mois_courant - revenus_mois_precedent) / revenus_mois_precedent * 100
        )
    else:
        evolution_revenus = 100.0 if revenus_mois_courant > 0 else 0.0
    
    # === LOCATAIRES EN RETARD ===
    locataires_en_cours = Locataire.objects.filter(
        chambre__maison__proprietaire=proprietaire,
        statut="EN_COURS",
    ).select_related("chambre", "chambre__maison")
    
    locataires_en_retard = []
    for locataire in locataires_en_cours:
        mois_impayes = get_mois_impayes(locataire)
        if mois_impayes:
            locataires_en_retard.append({
                "locataire": locataire,
                "mois_impayes": mois_impayes,
                "nb_mois_impaye": len(mois_impayes),
            })
    
    # Trier par nombre de mois impayés (décroissant)
    locataires_en_retard.sort(key=lambda x: x["nb_mois_impaye"], reverse=True)
    
    # === ALERTES AVANCE ===
    alertes_avance = []
    for locataire in locataires_en_cours:
        niveau = get_niveau_alerte(locataire)
        if niveau in ["critique", "urgent", "attention"]:
            alertes_avance.append({
                "locataire": locataire,
                "niveau": niveau,
                "mois_restants": round(get_avance_en_mois(locataire), 1),
                "avance_restante": locataire.avance_loyer,
            })
    
    # Trier par mois restants (croissant)
    alertes_avance.sort(key=lambda x: x["mois_restants"])
    
    # === PROBLÈMES OUVERTS ===
    problemes_ouverts = NoteChambre.objects.filter(
        chambre__maison__proprietaire=proprietaire,
        type="PROBLEME",
        statut="OUVERT",
    ).select_related("chambre", "chambre__maison").order_by("-cree_le")[:10]
    
    problemes_list = list(problemes_ouverts)
    
    return StatistiquesDashboard(
        nombre_maisons=nombre_maisons,
        chambres_total=chambres_total,
        chambres_occupees=chambres_occupees,
        chambres_libres=chambres_libres,
        taux_occupation=round(taux_occupation, 1),
        revenus_mois_courant=revenus_mois_courant,
        revenus_mois_precedent=revenus_mois_precedent,
        evolution_revenus=round(evolution_revenus, 1),
        nb_locataires_en_retard=len(locataires_en_retard),
        locataires_en_retard=locataires_en_retard,
        nb_alertes_avance=len(alertes_avance),
        alertes_avance=alertes_avance,
        nb_problemes_ouverts=len(problemes_list),
        problemes_ouverts=problemes_list,
    )


def get_nom_mois(numero: int) -> str:
    """Retourne le nom français du mois."""
    noms = [
        "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
    ]
    return noms[numero] if 1 <= numero <= 12 else ""
