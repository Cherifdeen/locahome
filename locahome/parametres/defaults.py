"""
Textes légaux par défaut pour les reçus PDF.

Ces textes sont utilisés lors de la création des paramètres d'un nouveau propriétaire.
Le propriétaire peut ensuite les modifier, supprimer ou compléter selon ses besoins.
"""

TEXTE_LEGAL_ENTREE_DEFAUT = """Je soussigné(e), reconnais avoir reçu du locataire mentionné ci-dessus les sommes indiquées au titre de :
- L'avance sur loyer correspondant au nombre de mois convenu
- La caution eau (remboursable à la sortie, déduction faite des consommations)
- La caution électricité (remboursable à la sortie, déduction faite des consommations)
- Le premier mois de loyer

Le locataire s'engage à :
• Occuper les lieux en bon père de famille
• Payer le loyer au plus tard à la date anniversaire de son entrée chaque mois
• Signaler tout problème ou dégradation dans les meilleurs délais
• Respecter le règlement intérieur de l'immeuble

En cas de retard de paiement, le montant du loyer sera automatiquement prélevé sur l'avance versée.

Le présent reçu est établi en double exemplaire, dont un remis au locataire."""

TEXTE_LEGAL_MENSUEL_DEFAUT = """Je soussigné(e), reconnais avoir reçu du locataire mentionné ci-dessus le paiement du loyer pour la période indiquée.

Ce paiement couvre uniquement le loyer mensuel. Les charges d'eau et d'électricité sont gérées séparément selon les relevés de consommation.

En cas de paiement partiel, le solde reste dû et devra être régularisé dans les plus brefs délais.

Le présent reçu est établi en double exemplaire."""

TEXTE_LEGAL_SORTIE_DEFAUT = """Le présent document constitue le décompte final de sortie du locataire.

CALCUL DU SOLDE :
• L'avance restante (après déduction des éventuels loyers impayés) est due au locataire
• La consommation d'électricité est calculée selon le relevé du compteur (entrée/sortie) × prix du KWh
• La caution électricité est restituée après déduction de la consommation réelle
• La caution eau est restituée après déduction des éventuelles factures impayées

REMISE DES CLÉS :
Le locataire atteste avoir remis l'ensemble des clés qui lui avaient été confiées.

ÉTAT DES LIEUX :
Les deux parties reconnaissent avoir effectué l'état des lieux de sortie. Toute dégradation constatée (hors usure normale) pourra faire l'objet d'une retenue sur le solde.

Le présent document est établi en double exemplaire et vaut quitus définitif entre les parties une fois signé par les deux parties."""


def get_defaults_parametres():
    """
    Retourne les valeurs par défaut pour les paramètres d'un propriétaire.
    """
    return {
        "prix_kwh": 110,
        "prix_location_defaut": 25000,
        "nombre_mois_avance": 3,
        "montant_caution_eau": 5000,
        "texte_legal_entree": TEXTE_LEGAL_ENTREE_DEFAUT.strip(),
        "texte_legal_mensuel": TEXTE_LEGAL_MENSUEL_DEFAUT.strip(),
        "texte_legal_sortie": TEXTE_LEGAL_SORTIE_DEFAUT.strip(),
    }
