from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from locahome.locataires.models import Locataire


@dataclass(frozen=True)
class PeriodeMensuelle:
    """
    Période d'un mois donné pour un locataire.

    Exemple : pour un locataire entré le 10 janvier,
    la période n°1 va du 10 janvier au 9 février,
    la période n°2 du 10 février au 9 mars, etc.
    """

    numero: int  # n-ième mois depuis l'entrée (1, 2, 3, ...)
    debut: date
    fin: date


def _ajouter_mois(d: date, n: int) -> date:
    """
    Ajoute n mois à une date en gérant les changements d'année.
    On reste sur un jour fixe (le jour de d), ou le dernier jour du mois si nécessaire.
    """
    mois_total = d.month - 1 + n
    annee = d.year + mois_total // 12
    mois = mois_total % 12 + 1

    # Gestion des jours en fin de mois
    # (ex : 31 janvier + 1 mois -> 28/29 février)
    from calendar import monthrange

    dernier_jour = monthrange(annee, mois)[1]
    jour = min(d.day, dernier_jour)
    return date(annee, mois, jour)


def construire_periode_mensuelle(date_entree: date, numero: int) -> PeriodeMensuelle:
    """
    Construit la période mensuelle n (1, 2, 3, ...) pour un locataire
    à partir de sa date d'entrée.
    """
    if numero < 1:
        raise ValueError("Le numéro de période doit être >= 1")

    debut = _ajouter_mois(date_entree, numero - 1)
    fin = _ajouter_mois(date_entree, numero) - date.resolution
    return PeriodeMensuelle(numero=numero, debut=debut, fin=fin)


def calculer_numero_periode(date_entree: date, date_reference: Optional[date] = None) -> int:
    """
    Calcule le numéro de période correspondant à une date de référence.

    Exemple :
        - date_entree = 10 janvier
        - du 10 janvier au 9 février -> période 1
        - du 10 février au 9 mars   -> période 2
    """
    if date_reference is None:
        date_reference = date.today()

    if date_reference < date_entree:
        raise ValueError("La date de référence est antérieure à la date d'entrée.")

    # On avance mois par mois jusqu'à dépasser la date de référence
    n = 1
    while True:
        periode = construire_periode_mensuelle(date_entree, n)
        if periode.debut <= date_reference <= periode.fin:
            return n
        n += 1


def est_en_retard(
    *,
    date_entree: date,
    numero_periode: int,
    date_reference: Optional[date],
    existe_paiement_mensuel_dans_periode: bool,
) -> bool:
    """
    Règle métier "paiement en retard" (version pure et testable).

    - Base : date d'entrée du locataire.
    - Le paiement du mois M doit être effectué avant date_limite = date_entree + n mois.
    - Retard s'il n'y a aucun paiement mensuel dans la période et que date_reference > date_limite.

    Paramètres :
        date_entree: date d'entrée du locataire.
        numero_periode: n-ième période mensuelle (1, 2, 3, ...).
        date_reference: date du jour (ou date à laquelle on vérifie).
        existe_paiement_mensuel_dans_periode:
            True si au moins un paiement de type "MENSUEL" existe avec une date
            comprise entre debut et fin de la période n.
    """
    if date_reference is None:
        date_reference = date.today()

    periode = construire_periode_mensuelle(date_entree, numero_periode)
    date_limite = periode.fin  # date_entree + n mois (fin de la période)

    if existe_paiement_mensuel_dans_periode:
        return False

    return date_reference > date_limite


def traiter_retards_locataire(locataire: "Locataire") -> list[dict]:
    """
    Vérifie tous les mois en retard pour un locataire et effectue
    les soustractions automatiques sur l'avance.
    
    Cette fonction est idempotente : elle ne soustrait que pour les mois
    qui n'ont pas encore été traités (pas de paiement ni de soustraction).
    
    Args:
        locataire: Le locataire à traiter
    
    Returns:
        Liste des périodes traitées avec les montants soustraits
    """
    from locahome.paiements.models import Paiement, TypePaiement
    from locahome.services.avance import soustraire_de_avance
    
    if locataire.statut != "EN_COURS":
        return []
    
    if locataire.date_entree > date.today():
        return []
    
    resultats = []
    prix_chambre = Decimal(locataire.chambre.prix_location)
    
    numero_actuel = calculer_numero_periode(locataire.date_entree, date.today())
    
    for numero in range(1, numero_actuel + 1):
        periode = construire_periode_mensuelle(locataire.date_entree, numero)
        
        paiement_existe = Paiement.objects.filter(
            locataire=locataire,
            type__in=[TypePaiement.MENSUEL, TypePaiement.ENTREE],
            mois=periode.debut.month,
            annee=periode.debut.year,
        ).exists()
        
        if paiement_existe:
            continue
        
        deja_soustrait = locataire.historique_soustractions.filter(
            motif__icontains=f"Période {numero}",
        ).exists()
        
        if deja_soustrait:
            continue
        
        if date.today() > periode.fin:
            motif = f"Retard loyer - Période {numero} ({periode.debut.strftime('%B %Y')})"
            soustraire_de_avance(locataire, prix_chambre, motif)
            resultats.append({
                "periode": numero,
                "mois": periode.debut.strftime("%B %Y"),
                "montant": prix_chambre,
            })
    
    return resultats


def get_mois_impayes(locataire: "Locataire") -> list[dict]:
    """
    Retourne la liste des mois impayés pour un locataire.
    
    Args:
        locataire: Le locataire concerné
    
    Returns:
        Liste des périodes impayées avec leurs détails
    """
    from locahome.paiements.models import Paiement, TypePaiement
    
    if locataire.statut != "EN_COURS":
        return []
    
    if locataire.date_entree > date.today():
        return []
    
    impayes = []
    numero_actuel = calculer_numero_periode(locataire.date_entree, date.today())
    
    for numero in range(1, numero_actuel + 1):
        periode = construire_periode_mensuelle(locataire.date_entree, numero)
        
        paiement_existe = Paiement.objects.filter(
            locataire=locataire,
            type__in=[TypePaiement.MENSUEL, TypePaiement.ENTREE],
            mois=periode.debut.month,
            annee=periode.debut.year,
        ).exists()
        
        if not paiement_existe and date.today() > periode.fin:
            impayes.append({
                "periode": numero,
                "mois": periode.debut.strftime("%B %Y"),
                "debut": periode.debut,
                "fin": periode.fin,
            })
    
    return impayes


