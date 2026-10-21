from django.db import models

from locahome.comptes.models import Proprietaire


class TypeMaison(models.TextChoices):
    MAISON = "MAISON", "Maison"
    APPARTEMENT = "APPARTEMENT", "Appartement"
    STUDIO = "STUDIO", "Studio"
    VILLA = "VILLA", "Villa"
    DUPLEX = "DUPLEX", "Duplex"
    AUTRE = "AUTRE", "Autre"


class Maison(models.Model):
    """
    Représente une maison/immeuble appartenant à un propriétaire.
    Chaque maison contient plusieurs chambres à louer.
    """

    proprietaire = models.ForeignKey(
        Proprietaire,
        on_delete=models.CASCADE,
        related_name="maisons",
    )
    nom = models.CharField(
        max_length=100,
        help_text="Nom ou identifiant de la maison.",
    )
    quartier = models.CharField(
        max_length=100,
        help_text="Quartier où se situe la maison.",
    )
    type_maison = models.CharField(
        max_length=20,
        choices=TypeMaison.choices,
        default=TypeMaison.MAISON,
    )
    adresse = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    photo = models.ImageField(
        upload_to="maisons/",
        null=True,
        blank=True,
    )

    cree_le = models.DateTimeField(auto_now_add=True)
    mis_a_jour_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Maison"
        verbose_name_plural = "Maisons"
        ordering = ["-cree_le"]

    def __str__(self) -> str:
        return f"{self.nom} ({self.quartier})"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("maisons:detail", kwargs={"pk": self.pk})

    @property
    def nombre_chambres_total(self) -> int:
        """Retourne le nombre total de chambres dans cette maison."""
        return self.chambres.count()

    @property
    def nombre_chambres_libres(self) -> int:
        """Retourne le nombre de chambres libres dans cette maison."""
        return self.chambres.filter(statut="LIBRE").count()

    @property
    def nombre_chambres_occupees(self) -> int:
        """Retourne le nombre de chambres occupées dans cette maison."""
        return self.chambres.filter(statut="OCCUPEE").count()

    @property
    def prix_minimum(self):
        """Retourne le prix de la chambre la moins chère."""
        chambre = self.chambres.order_by("prix_location").first()
        return chambre.prix_location if chambre else None
