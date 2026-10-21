from django.db import models

from locahome.comptes.models import Proprietaire


class ParametresProprietaire(models.Model):
    """
    Paramètres définis par chaque propriétaire.
    Chaque propriétaire a ses propres paramètres.
    """

    proprietaire = models.OneToOneField(
        Proprietaire,
        on_delete=models.CASCADE,
        related_name="parametres",
    )

    # Textes légaux utilisés dans les reçus PDF
    texte_legal_entree = models.TextField(blank=True)
    texte_legal_mensuel = models.TextField(blank=True)
    texte_legal_sortie = models.TextField(blank=True)

    prix_kwh = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Prix d'un KWh.",
    )
    prix_location_defaut = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Prix de location par défaut pour une chambre.",
    )

    # Paramètres d'entrée
    nombre_mois_avance = models.PositiveSmallIntegerField(
        default=3,
        help_text="Nombre de mois d'avance requis à l'entrée.",
    )
    montant_caution_eau = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant de la caution eau à l'entrée.",
    )

    # Mise en forme des PDF
    logo = models.ImageField(
        upload_to="logos/",
        null=True,
        blank=True,
    )
    signature = models.ImageField(
        upload_to="signatures/",
        null=True,
        blank=True,
    )

    cree_le = models.DateTimeField(auto_now_add=True)
    mis_a_jour_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paramètres du propriétaire"
        verbose_name_plural = "Paramètres des propriétaires"

    def __str__(self) -> str:
        return f"Paramètres - {self.proprietaire.nom_complet}"

