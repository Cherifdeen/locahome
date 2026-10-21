"""
Service de gestion des avances locataires.

Gère le calcul, la soustraction et les alertes sur les avances de loyer.
"""

from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from locahome.chambres.models import Chambre
    from locahome.locataires.models import Locataire


def calculer_avance_requise(chambre: "Chambre", nb_mois: int) -> Decimal:
    """
    Calcule le montant d'avance requis pour une chambre.
    
    Args:
        chambre: La chambre concernée
        nb_mois: Nombre de mois d'avance requis
    
    Returns:
        Montant total de l'avance (prix_location × nb_mois)
    """
    return Decimal(chambre.prix_location) * nb_mois


def get_avance_restante(locataire: "Locataire") -> Decimal:
    """
    Retourne le montant restant de l'avance d'un locataire.
    
    Args:
        locataire: Le locataire concerné
    
    Returns:
        Montant restant de l'avance
    """
    return Decimal(locataire.avance_loyer)


def get_avance_en_mois(locataire: "Locataire") -> Decimal:
    """
    Retourne l'avance restante exprimée en nombre de mois.
    
    Args:
        locataire: Le locataire concerné
    
    Returns:
        Nombre de mois d'avance restants (peut être décimal)
    """
    prix_chambre = Decimal(locataire.chambre.prix_location)
    if prix_chambre == 0:
        return Decimal("0")
    return get_avance_restante(locataire) / prix_chambre


def verifier_alerte_avance(locataire: "Locataire") -> bool:
    """
    Vérifie si l'avance du locataire nécessite une alerte.
    
    Alerte si l'avance restante est inférieure ou égale à 1 mois de loyer.
    
    Args:
        locataire: Le locataire concerné
    
    Returns:
        True si alerte nécessaire (avance ≤ 1 mois)
    """
    return get_avance_en_mois(locataire) <= Decimal("1")


def get_niveau_alerte(locataire: "Locataire") -> str:
    """
    Retourne le niveau d'alerte pour l'avance d'un locataire.
    
    Args:
        locataire: Le locataire concerné
    
    Returns:
        'critique' si avance = 0
        'urgent' si avance ≤ 1 mois
        'attention' si avance ≤ 2 mois
        'ok' sinon
    """
    mois_restants = get_avance_en_mois(locataire)
    
    if mois_restants <= Decimal("0"):
        return "critique"
    elif mois_restants <= Decimal("1"):
        return "urgent"
    elif mois_restants <= Decimal("2"):
        return "attention"
    return "ok"


def soustraire_de_avance(locataire: "Locataire", montant: Decimal, motif: str = "") -> Decimal:
    """
    Soustrait un montant de l'avance du locataire et enregistre l'historique.
    
    Args:
        locataire: Le locataire concerné
        montant: Montant à soustraire
        motif: Raison de la soustraction (ex: "Retard mois Mars 2024")
    
    Returns:
        Nouveau montant de l'avance après soustraction
    """
    from locahome.locataires.models import HistoriqueSoustraction
    
    montant = Decimal(montant)
    ancien_montant = Decimal(locataire.avance_loyer)
    nouveau_montant = max(Decimal("0"), ancien_montant - montant)
    
    locataire.avance_loyer = nouveau_montant
    locataire.save(update_fields=["avance_loyer", "mis_a_jour_le"])
    
    HistoriqueSoustraction.objects.create(
        locataire=locataire,
        montant=montant,
        avance_avant=ancien_montant,
        avance_apres=nouveau_montant,
        motif=motif,
    )
    
    return nouveau_montant


def rembourser_avance(locataire: "Locataire", montant: Decimal, motif: str = "") -> Decimal:
    """
    Ajoute un montant à l'avance du locataire (remboursement/ajout).
    
    Args:
        locataire: Le locataire concerné
        montant: Montant à ajouter
        motif: Raison de l'ajout
    
    Returns:
        Nouveau montant de l'avance après ajout
    """
    from locahome.locataires.models import HistoriqueSoustraction
    
    montant = Decimal(montant)
    ancien_montant = Decimal(locataire.avance_loyer)
    nouveau_montant = ancien_montant + montant
    
    locataire.avance_loyer = nouveau_montant
    locataire.save(update_fields=["avance_loyer", "mis_a_jour_le"])
    
    HistoriqueSoustraction.objects.create(
        locataire=locataire,
        montant=-montant,  # Négatif pour indiquer un ajout
        avance_avant=ancien_montant,
        avance_apres=nouveau_montant,
        motif=motif or "Ajout à l'avance",
    )
    
    return nouveau_montant
