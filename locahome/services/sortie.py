"""
Service de gestion de la sortie d'un locataire.

Gère le calcul du solde final, incluant:
- Défalcation des mois impayés sur l'avance
- Calcul électricité (KWh pour carte, facture pour classique)
- Calcul facture eau
- Solde dû au locataire ou à payer par le locataire
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from locahome.locataires.models import Locataire


@dataclass
class DetailElectricite:
    """Détails du calcul électricité."""
    type_decompteur: str  # "CARTE" ou "CLASSIQUE"
    # Pour décompteur à carte
    kwh_entree: Decimal = Decimal("0")
    kwh_sortie: Decimal = Decimal("0")
    difference_kwh: Decimal = Decimal("0")
    prix_kwh: Decimal = Decimal("0")
    montant_difference: Decimal = Decimal("0")  # difference_kwh * prix_kwh
    # Commun
    montant_a_payer: Decimal = Decimal("0")  # Ce que le locataire doit
    caution_initiale: Decimal = Decimal("0")
    # Résultat
    du_au_locataire: Decimal = Decimal("0")  # Caution à rendre (si conso < caution)
    a_payer_par_locataire: Decimal = Decimal("0")  # Dette (si conso > caution)
    defalque_sur_avance: Decimal = Decimal("0")


@dataclass
class DetailEau:
    """Détails du calcul eau."""
    montant_facture: Decimal = Decimal("0")
    caution_initiale: Decimal = Decimal("0")
    # Résultat: solde = caution - facture
    solde: Decimal = Decimal("0")  # Positif = dû au locataire, Négatif = locataire doit
    defalque_sur_avance: Decimal = Decimal("0")
    
    @property
    def du_au_locataire(self) -> Decimal:
        """Montant dû au locataire (si solde positif)."""
        return max(Decimal("0"), self.solde)
    
    @property
    def a_payer_par_locataire(self) -> Decimal:
        """Montant à payer par le locataire (si solde négatif après défalcation)."""
        if self.solde < 0:
            return abs(self.solde) - self.defalque_sur_avance
        return Decimal("0")


@dataclass
class DetailDommages:
    """Détails des dommages causés par le locataire."""
    description: str = ""
    montant: Decimal = Decimal("0")
    defalque_sur_avance: Decimal = Decimal("0")
    a_payer_par_locataire: Decimal = Decimal("0")


@dataclass
class DetailAvance:
    """Détails des défalcations sur l'avance."""
    montant_initial: Decimal = Decimal("0")
    defalcation_loyers_impayes: Decimal = Decimal("0")
    defalcation_electricite: Decimal = Decimal("0")
    defalcation_eau: Decimal = Decimal("0")
    defalcation_dommages: Decimal = Decimal("0")
    montant_final: Decimal = Decimal("0")


@dataclass
class ResultatSortie:
    """Résultat complet du calcul de sortie."""
    avance: DetailAvance
    electricite: DetailElectricite
    eau: DetailEau
    dommages: DetailDommages
    
    # Solde final
    total_du_au_locataire: Decimal = Decimal("0")
    total_a_payer_par_locataire: Decimal = Decimal("0")
    
    # Résumé
    @property
    def solde_final(self) -> Decimal:
        """Positif = dû au locataire, Négatif = à payer par locataire."""
        return self.total_du_au_locataire - self.total_a_payer_par_locataire


def calculer_sortie(
    locataire: "Locataire",
    *,
    # Électricité
    kwh_sortie: Optional[Decimal] = None,
    prix_kwh: Optional[Decimal] = None,
    montant_facture_electricite: Optional[Decimal] = None,
    # Eau
    montant_facture_eau: Decimal = Decimal("0"),
    # Mois impayés
    montant_loyers_impayes: Decimal = Decimal("0"),
    # Dommages
    description_dommages: str = "",
    montant_dommages: Decimal = Decimal("0"),
) -> ResultatSortie:
    """
    Calcule le solde final lors de la sortie d'un locataire.
    
    Règles:
    1. Les loyers impayés sont d'abord défalqués de l'avance
    2. Pour l'électricité (CARTE):
       - Différence = kwh_sortie - kwh_entree
       - Montant = différence * prix_kwh
       - Si montant <= caution: on rend (caution - montant) au locataire
       - Si montant > caution: locataire doit (montant - caution), défalqué sur avance
    3. Pour l'électricité (CLASSIQUE) et l'eau:
       - Si facture <= caution: on rend (caution - facture) au locataire
       - Si facture > caution: locataire doit (facture - caution), défalqué sur avance
    4. Solde final = somme des "dû au locataire" - somme des "à payer par locataire"
    """
    from locahome.chambres.models import TypeDecompteur
    
    chambre = locataire.chambre
    type_decompteur = chambre.type_decompteur
    
    # === AVANCE ===
    avance_initiale = Decimal(locataire.avance_loyer)
    avance_restante = avance_initiale
    
    # Défalcation des loyers impayés
    defalcation_loyers = min(montant_loyers_impayes, avance_restante)
    avance_restante -= defalcation_loyers
    
    # === ÉLECTRICITÉ ===
    caution_elec = Decimal(locataire.caution_electricite)
    defalcation_elec = Decimal("0")
    elec_du_au_locataire = Decimal("0")
    elec_a_payer = Decimal("0")
    
    if type_decompteur == TypeDecompteur.CARTE:
        # Décompteur à carte: calcul par KWh
        # Le locataire recharge le compteur. À la sortie:
        # - Si sortie > entrée: il a un crédit restant → propriétaire lui doit
        # - Si sortie < entrée: il a consommé son crédit → il doit payer
        kwh_entree_val = Decimal(locataire.kwh_entree)
        kwh_sortie_val = Decimal(kwh_sortie or 0)
        prix_kwh_val = Decimal(prix_kwh or 0)
        difference = kwh_sortie_val - kwh_entree_val
        montant_difference = abs(difference) * prix_kwh_val
        
        if difference >= 0:
            # Différence positive: le locataire a un crédit → propriétaire lui doit
            # On lui rend: caution + valeur du crédit restant
            elec_du_au_locataire = caution_elec + montant_difference
        else:
            # Différence négative: le locataire a consommé → il doit payer
            # Montant à payer = valeur de la consommation
            # D'abord couvert par la caution
            if montant_difference <= caution_elec:
                # Caution suffit → on rend le reste
                elec_du_au_locataire = caution_elec - montant_difference
            else:
                # Caution ne suffit pas → locataire doit le reste
                dette_elec = montant_difference - caution_elec
                # Défalquer sur l'avance si possible
                defalcation_elec = min(dette_elec, avance_restante)
                avance_restante -= defalcation_elec
                elec_a_payer = dette_elec - defalcation_elec
        
        detail_elec = DetailElectricite(
            type_decompteur="CARTE",
            kwh_entree=kwh_entree_val,
            kwh_sortie=kwh_sortie_val,
            difference_kwh=difference,
            prix_kwh=prix_kwh_val,
            montant_difference=montant_difference,
            montant_a_payer=montant_difference,
            caution_initiale=caution_elec,
            du_au_locataire=elec_du_au_locataire,
            a_payer_par_locataire=elec_a_payer,
            defalque_sur_avance=defalcation_elec,
        )
    else:
        # Décompteur classique: montant facture directement
        montant_elec = Decimal(montant_facture_electricite or 0)
        
        if montant_elec <= caution_elec:
            elec_du_au_locataire = caution_elec - montant_elec
        else:
            dette_elec = montant_elec - caution_elec
            defalcation_elec = min(dette_elec, avance_restante)
            avance_restante -= defalcation_elec
            elec_a_payer = dette_elec - defalcation_elec
        
        detail_elec = DetailElectricite(
            type_decompteur="CLASSIQUE",
            montant_a_payer=montant_elec,
            caution_initiale=caution_elec,
            du_au_locataire=elec_du_au_locataire,
            a_payer_par_locataire=elec_a_payer,
            defalque_sur_avance=defalcation_elec,
        )
    
    # === EAU ===
    caution_eau = Decimal(locataire.caution_eau)
    montant_eau = Decimal(montant_facture_eau)
    
    # Solde = caution - facture
    # Positif = propriétaire doit au locataire
    # Négatif = locataire doit au propriétaire
    solde_eau = caution_eau - montant_eau
    defalcation_eau = Decimal("0")
    
    if solde_eau < 0:
        # Locataire doit au propriétaire, défalquer sur avance si possible
        dette_eau = abs(solde_eau)
        defalcation_eau = min(dette_eau, avance_restante)
        avance_restante -= defalcation_eau
    
    detail_eau = DetailEau(
        montant_facture=montant_eau,
        caution_initiale=caution_eau,
        solde=solde_eau,
        defalque_sur_avance=defalcation_eau,
    )
    
    # === DOMMAGES ===
    montant_dommages_val = Decimal(montant_dommages or 0)
    defalcation_dommages = Decimal("0")
    dommages_a_payer = Decimal("0")
    
    if montant_dommages_val > 0:
        # Les dommages sont d'abord défalqués sur l'avance restante
        defalcation_dommages = min(montant_dommages_val, avance_restante)
        avance_restante -= defalcation_dommages
        # Ce qui n'est pas couvert reste à payer par le locataire
        dommages_a_payer = montant_dommages_val - defalcation_dommages
    
    detail_dommages = DetailDommages(
        description=description_dommages,
        montant=montant_dommages_val,
        defalque_sur_avance=defalcation_dommages,
        a_payer_par_locataire=dommages_a_payer,
    )
    
    # === AVANCE FINALE ===
    detail_avance = DetailAvance(
        montant_initial=avance_initiale,
        defalcation_loyers_impayes=defalcation_loyers,
        defalcation_electricite=defalcation_elec,
        defalcation_eau=defalcation_eau,
        defalcation_dommages=defalcation_dommages,
        montant_final=avance_restante,
    )
    
    # === SOLDE FINAL ===
    # Dû au locataire (ROUGE): avance restante + reste cautions eau/elec
    total_du = avance_restante + elec_du_au_locataire + detail_eau.du_au_locataire
    
    # À payer par locataire (VERT): dettes non couvertes
    loyers_non_couverts = montant_loyers_impayes - defalcation_loyers
    total_a_payer = (
        elec_a_payer 
        + detail_eau.a_payer_par_locataire 
        + loyers_non_couverts 
        + dommages_a_payer
    )
    
    return ResultatSortie(
        avance=detail_avance,
        electricite=detail_elec,
        eau=detail_eau,
        dommages=detail_dommages,
        total_du_au_locataire=total_du,
        total_a_payer_par_locataire=total_a_payer,
    )
