from datetime import date
from decimal import Decimal

from django.db import models

from locahome.chambres.models import Chambre
from locahome.services.kwh import calculer_resultat_kwh
from locahome.services.paiements import (
    PeriodeMensuelle,
    calculer_numero_periode,
    construire_periode_mensuelle,
    est_en_retard,
)


class StatutLocataire(models.TextChoices):
    EN_ATTENTE = "EN_ATTENTE", "En attente"
    EN_COURS = "EN_COURS", "En cours"
    SORTI = "SORTI", "Sorti"


class Locataire(models.Model):
    """
    Représente un locataire occupant (ou ayant occupé) une chambre.
    L'historique sera déduit de l'ensemble des enregistrements liés à une chambre.
    """

    nom_complet = models.CharField(max_length=150)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.CharField(max_length=255, blank=True)

    chambre = models.ForeignKey(
        Chambre,
        related_name="locataires",
        on_delete=models.PROTECT,
        help_text="Chambre occupée par ce locataire.",
    )

    date_entree = models.DateField()
    date_sortie = models.DateField(null=True, blank=True)

    # Gestion de l'électricité
    kwh_entree = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Index KWh relevé à l'entrée.",
    )

    # Loyer - Avance (garantie)
    avance_initiale = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant initial de l'avance (X mois × prix chambre).",
    )
    avance_loyer = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant restant de l'avance (après soustractions éventuelles).",
    )

    # Cautions (payées à l'entrée)
    caution_eau = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant de la caution eau payée à l'entrée.",
    )
    caution_electricite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant de la caution électricité payée à l'entrée.",
    )

    # Nombre de clés remises
    nombre_cles = models.PositiveSmallIntegerField(
        default=1,
        help_text="Nombre de clés remises au locataire.",
    )

    statut = models.CharField(
        max_length=20,
        choices=StatutLocataire.choices,
        default=StatutLocataire.EN_COURS,
    )

    cree_le = models.DateTimeField(auto_now_add=True)
    mis_a_jour_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_entree", "nom_complet"]

    def __str__(self) -> str:
        return self.nom_complet

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("locataires:detail", kwargs={"pk": self.pk})

    # ---------------------------
    # Méthodes de confort - Retards
    # ---------------------------
    def get_periode_mensuelle(self, numero: int) -> PeriodeMensuelle:
        """
        Retourne la période mensuelle n pour ce locataire.
        """
        return construire_periode_mensuelle(self.date_entree, numero)

    def est_en_retard_pour_periode(self, numero: int, date_reference: date | None = None) -> bool:
        """
        Indique si le locataire est en retard pour la période n.

        La fonction va vérifier s'il existe un paiement MENSUEL dans la période.
        """
        from locahome.paiements.models import Paiement, TypePaiement

        periode = self.get_periode_mensuelle(numero)

        existe_paiement = Paiement.objects.filter(
            locataire=self,
            type=TypePaiement.MENSUEL,
            date_paiement__gte=periode.debut,
            date_paiement__lte=periode.fin,
        ).exists()

        return est_en_retard(
            date_entree=self.date_entree,
            numero_periode=numero,
            date_reference=date_reference,
            existe_paiement_mensuel_dans_periode=existe_paiement,
        )

    def est_actuellement_en_retard(self, date_reference: date | None = None) -> bool:
        """
        Indique si le locataire est en retard à la date donnée (ou aujourd'hui).
        """
        if date_reference is None:
            date_reference = date.today()

        numero = calculer_numero_periode(self.date_entree, date_reference)
        return self.est_en_retard_pour_periode(numero, date_reference=date_reference)

    # ---------------------------
    # Méthodes de confort - KWh
    # ---------------------------
    def calculer_resultat_kwh(
        self,
        *,
        kwh_sortie: Decimal,
        prix_kwh: Decimal,
        avance: Decimal | None = None,
    ):
        """
        Utilitaire pour calculer la consommation KWh à partir :
            - de kwh_entree stocké sur le locataire
            - de kwh_sortie fourni (souvent lors de la sortie)
            - du prix_kwh (provenant des paramètres)
            - de l'avance (par défaut caution_electricite du locataire)
        """
        if avance is None:
            avance = self.caution_electricite

        return calculer_resultat_kwh(
            kwh_entree=Decimal(self.kwh_entree),
            kwh_sortie=Decimal(kwh_sortie),
            prix_kwh=Decimal(prix_kwh),
            avance=Decimal(avance),
        )


class HistoriqueSoustraction(models.Model):
    """
    Historique des soustractions effectuées sur l'avance d'un locataire.
    Permet de tracer chaque déduction (retard, pénalité, etc.).
    """

    locataire = models.ForeignKey(
        Locataire,
        related_name="historique_soustractions",
        on_delete=models.CASCADE,
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Montant soustrait (positif) ou ajouté (négatif).",
    )
    avance_avant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Montant de l'avance avant la soustraction.",
    )
    avance_apres = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Montant de l'avance après la soustraction.",
    )
    motif = models.CharField(
        max_length=255,
        blank=True,
        help_text="Raison de la soustraction (ex: Retard mois Mars 2024).",
    )
    date_operation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_operation"]
        verbose_name = "Historique soustraction"
        verbose_name_plural = "Historiques soustractions"

    def __str__(self) -> str:
        action = "Soustraction" if self.montant > 0 else "Ajout"
        return f"{action} {abs(self.montant)} FCFA - {self.locataire.nom_complet}"


