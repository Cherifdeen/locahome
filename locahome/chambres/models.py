from django.db import models

from locahome.maisons.models import Maison


class StatutChambre(models.TextChoices):
    LIBRE = "LIBRE", "Libre"
    OCCUPEE = "OCCUPEE", "Occupée"


class TypeDecompteur(models.TextChoices):
    CARTE = "CARTE", "Décompteur à carte"
    CLASSIQUE = "CLASSIQUE", "Décompteur classique"


class Chambre(models.Model):
    """
    Représente une chambre mise en location.
    L'historique des locataires sera accessible via la relation inverse
    depuis le modèle Locataire.
    """

    maison = models.ForeignKey(
        Maison,
        on_delete=models.CASCADE,
        related_name="chambres",
        help_text="Maison à laquelle appartient cette chambre.",
    )
    numero = models.CharField(
        max_length=20,
        help_text="Identifiant ou numéro de la chambre.",
    )
    nom = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nom ou libellé de la chambre (facultatif).",
    )
    statut = models.CharField(
        max_length=20,
        choices=StatutChambre.choices,
        default=StatutChambre.LIBRE,
    )
    prix_location = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Prix du loyer mensuel pour cette chambre.",
    )
    caution_eau = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant de la caution eau pour cette chambre.",
    )
    caution_electricite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant de la caution électricité pour cette chambre.",
    )
    type_decompteur = models.CharField(
        max_length=20,
        choices=TypeDecompteur.choices,
        default=TypeDecompteur.CARTE,
        help_text="Type de décompteur électrique utilisé.",
    )
    description = models.TextField(blank=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    mis_a_jour_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["numero"]
        unique_together = ["maison", "numero"]

    def __str__(self) -> str:
        return f"Chambre {self.numero}" if not self.nom else f"{self.numero} - {self.nom}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("chambres:detail", kwargs={"pk": self.pk})

    @property
    def locataire_actuel(self):
        """Retourne le locataire actuellement en cours, s'il existe."""
        return self.locataires.filter(statut="EN_COURS").order_by("-date_entree").first()


class TypeNote(models.TextChoices):
    NOTE = "NOTE", "Note"
    PROBLEME = "PROBLEME", "Problème"


class StatutNote(models.TextChoices):
    OUVERT = "OUVERT", "Ouvert"
    RESOLU = "RESOLU", "Résolu"


class NoteChambre(models.Model):
    """
    Note ou problème associé à une chambre.
    Permet de suivre les problèmes signalés et les remarques diverses.
    """

    chambre = models.ForeignKey(
        Chambre,
        related_name="notes",
        on_delete=models.CASCADE,
    )
    type = models.CharField(
        max_length=20,
        choices=TypeNote.choices,
        default=TypeNote.NOTE,
    )
    statut = models.CharField(
        max_length=20,
        choices=StatutNote.choices,
        default=StatutNote.OUVERT,
    )
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    mis_a_jour_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-cree_le"]

    def __str__(self) -> str:
        return f"{self.get_type_display()} - {self.chambre} - {self.titre}"


