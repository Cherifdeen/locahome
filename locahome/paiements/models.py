from django.db import models

from locahome.locataires.models import Locataire


class TypePaiement(models.TextChoices):
    FORMALITES = "FORMALITES", "Formalités d'entrée"
    ENTREE = "ENTREE", "Premier mois"
    MENSUEL = "MENSUEL", "Mensuel"
    SORTIE = "SORTIE", "Sortie"


class Paiement(models.Model):
    """
    Paiement effectué par un locataire.
    Sera lié aux reçus PDF générés.
    """

    locataire = models.ForeignKey(
        Locataire,
        related_name="paiements",
        on_delete=models.CASCADE,
    )
    type = models.CharField(
        max_length=20,
        choices=TypePaiement.choices,
    )

    montant_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    reste = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant restant à payer pour la période concernée.",
    )

    # Utile pour les paiements mensuels
    mois = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Mois concerné (1-12) pour les paiements mensuels.",
    )
    annee = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Année concernée pour les paiements mensuels.",
    )

    date_paiement = models.DateField()
    details_sortie = models.JSONField(
        default=dict,
        blank=True,
        help_text="Instantané du calcul et des montants confirmés pour une sortie.",
    )

    # Lien éventuel vers le fichier PDF généré
    recu_pdf = models.FileField(
        upload_to="recus/",
        null=True,
        blank=True,
    )

    cree_le = models.DateTimeField(auto_now_add=True)
    mis_a_jour_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_paiement"]

    def __str__(self) -> str:
        return f"{self.locataire} - {self.get_type_display()} - {self.date_paiement}"


class ConsommationKwh(models.Model):
    """
    Détail de la consommation KWh associée à un locataire,
    généralement utilisé lors de la sortie.
    """

    locataire = models.OneToOneField(
        Locataire,
        related_name="consommation_kwh",
        on_delete=models.CASCADE,
    )

    kwh_entree = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Index KWh à l'entrée.",
    )
    kwh_sortie = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Index KWh à la sortie.",
    )

    consommation = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Consommation totale en KWh (sortie - entrée).",
    )
    montant_conso = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant total de la consommation (consommation * prix_kwh).",
    )

    avance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant avancé pour l'électricité.",
    )
    dette = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant dû par le locataire (si consommation > avance).",
    )
    remboursement = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant à rembourser au locataire (si avance > consommation).",
    )

    cree_le = models.DateTimeField(auto_now_add=True)
    mis_a_jour_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Consommation KWh"
        verbose_name_plural = "Consommations KWh"

    def __str__(self) -> str:
        return f"Consommation KWh - {self.locataire}"


