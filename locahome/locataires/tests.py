from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from locahome.chambres.models import Chambre
from locahome.comptes.models import Proprietaire
from locahome.maisons.models import Maison
from locahome.paiements.models import Paiement, TypePaiement
from .models import Locataire, StatutLocataire


class LocataireTenantIsolationTests(TestCase):
    def setUp(self):
        self.proprietaire_user = User.objects.create_user(
            username="proprietaire",
            password="test-password",
        )
        self.proprietaire = Proprietaire.objects.create(
            user=self.proprietaire_user,
            nom_complet="Propriétaire A",
        )
        autre_user = User.objects.create_user(
            username="autre-proprietaire",
            password="test-password",
        )
        autre_proprietaire = Proprietaire.objects.create(
            user=autre_user,
            nom_complet="Propriétaire B",
        )

        self.chambre = self.creer_chambre(self.proprietaire, "A")
        self.autre_chambre = self.creer_chambre(autre_proprietaire, "B")
        self.locataire = Locataire.objects.create(
            nom_complet="Locataire A",
            chambre=self.chambre,
            date_entree=date.today(),
            kwh_entree=Decimal("0"),
        )
        self.client.force_login(self.proprietaire_user)

    @staticmethod
    def creer_chambre(proprietaire, suffixe):
        maison = Maison.objects.create(
            proprietaire=proprietaire,
            nom=f"Maison {suffixe}",
            quartier="Centre",
        )
        return Chambre.objects.create(
            maison=maison,
            numero="1",
            prix_location=Decimal("50000"),
        )

    def test_cannot_reassign_tenant_to_another_owners_room(self):
        response = self.client.post(
            reverse("locataires:modifier", kwargs={"pk": self.locataire.pk}),
            {
                "nom_complet": self.locataire.nom_complet,
                "telephone": "",
                "email": "",
                "adresse": "",
                "chambre": self.autre_chambre.pk,
                "date_entree": self.locataire.date_entree.isoformat(),
                "date_sortie": "",
                "kwh_entree": "0",
                "caution_eau": "0",
                "caution_electricite": "0",
                "avance_loyer": "0",
                "statut": "EN_COURS",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.locataire.refresh_from_db()
        self.assertEqual(self.locataire.chambre, self.chambre)

    def creer_locataire_en_attente(self):
        return Locataire.objects.create(
            nom_complet="Locataire en attente",
            chambre=self.chambre,
            date_entree=date.today(),
            kwh_entree=Decimal("0"),
            statut=StatutLocataire.EN_ATTENTE,
        )

    def donnees_premier_mois(self, montant):
        return {
            "montant_paye": str(montant),
            "date_paiement": date.today().isoformat(),
            "confirmer_paiement": "on",
        }

    def test_partial_first_month_payment_does_not_activate_tenant(self):
        locataire = self.creer_locataire_en_attente()

        response = self.client.post(
            reverse("locataires:premier_mois", kwargs={"locataire_id": locataire.pk}),
            self.donnees_premier_mois("25000"),
        )

        self.assertEqual(response.status_code, 200)
        locataire.refresh_from_db()
        self.chambre.refresh_from_db()
        self.assertEqual(locataire.statut, StatutLocataire.EN_ATTENTE)
        self.assertEqual(self.chambre.statut, Chambre._meta.get_field("statut").default)
        self.assertFalse(
            Paiement.objects.filter(locataire=locataire, type=TypePaiement.ENTREE).exists()
        )
        self.assertIn("montant_paye", response.context["form"].errors)

    def test_exact_first_month_payment_activates_tenant(self):
        locataire = self.creer_locataire_en_attente()

        response = self.client.post(
            reverse("locataires:premier_mois", kwargs={"locataire_id": locataire.pk}),
            self.donnees_premier_mois("50000"),
        )

        self.assertRedirects(
            response,
            reverse("locataires:detail", kwargs={"pk": locataire.pk}),
        )
        locataire.refresh_from_db()
        self.chambre.refresh_from_db()
        self.assertEqual(locataire.statut, StatutLocataire.EN_COURS)
        self.assertEqual(self.chambre.statut, "OCCUPEE")
        paiement = Paiement.objects.get(locataire=locataire, type=TypePaiement.ENTREE)
        self.assertEqual(paiement.montant_paye, Decimal("50000"))
        self.assertEqual(paiement.reste, Decimal("0"))
