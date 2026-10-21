from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class ResultatKwh:
    """
    Résultat complet du calcul KWh pour un locataire.
    """

    consommation: Decimal
    montant_conso: Decimal
    dette: Decimal
    remboursement: Decimal


def calculer_consommation(kwh_entree: Decimal, kwh_sortie: Decimal) -> Decimal:
    """
    consommation = kwh_sortie - kwh_entree
    """
    return kwh_sortie - kwh_entree


def calculer_montant_conso(consommation: Decimal, prix_kwh: Decimal) -> Decimal:
    """
    montant_conso = consommation * prix_kwh
    """
    return consommation * prix_kwh


def calculer_dette_ou_remboursement(
    *, montant_conso: Decimal, avance: Decimal
) -> tuple[Decimal, Decimal]:
    """
    Règles métier :
        - Si coût consommation > avance → dette = montant_conso - avance
        - Si coût consommation < avance → remboursement = avance - montant_conso
        - Sinon ni dette ni remboursement.
    """
    if montant_conso > avance:
        return montant_conso - avance, Decimal("0")
    if montant_conso < avance:
        return Decimal("0"), avance - montant_conso
    return Decimal("0"), Decimal("0")


def calculer_resultat_kwh(
    *,
    kwh_entree: Decimal,
    kwh_sortie: Decimal,
    prix_kwh: Decimal,
    avance: Optional[Decimal] = None,
) -> ResultatKwh:
    """
    Fonction haut niveau qui applique toutes les règles :

        consommation = sortie - entrée
        montant = consommation × prix_kwh

        Si avance fournie :
            - Si montant_conso > avance → dette
            - Si montant_conso < avance → remboursement
        Sinon :
            - Tout le montant_conso est à payer (dette).
    """
    if avance is None:
        avance = Decimal("0")

    conso = calculer_consommation(kwh_entree, kwh_sortie)
    montant = calculer_montant_conso(conso, prix_kwh)

    if avance == 0:
        # Cas 2 du cahier : aucune avance, tout est à payer à la sortie
        dette = montant
        remboursement = Decimal("0")
    else:
        dette, remboursement = calculer_dette_ou_remboursement(
            montant_conso=montant,
            avance=avance,
        )

    return ResultatKwh(
        consommation=conso,
        montant_conso=montant,
        dette=dette,
        remboursement=remboursement,
    )



