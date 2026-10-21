from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from locahome.chambres.models import Chambre
from locahome.comptes.models import Proprietaire
from locahome.locataires.models import Locataire
from locahome.locataires.models import StatutLocataire
from locahome.maisons.models import Maison
from .models import Paiement, TypePaiement


class PaiementTenantIsolationTests(TestCase):
    def setUp(self):
        self.proprietaire_user = User.objects.create_user(
            username="proprietaire",
            password="test-password",
        )
        self.proprietaire = Proprietaire.objects.create(
            user=self.proprietaire_user,
            nom_complet="Propriétaire A",
        )
        self.autre_proprietaire_user = User.objects.create_user(
            username="autre-proprietaire",
            password="test-password",
        )
        self.autre_proprietaire = Proprietaire.objects.create(
            user=self.autre_proprietaire_user,
            nom_complet="Propriétaire B",
        )

        self.chambre = self.creer_chambre(self.proprietaire, "A")
        self.autre_chambre = self.creer_chambre(self.autre_proprietaire, "B")
        self.locataire = self.creer_locataire(self.chambre, "Locataire A")
        self.autre_locataire = self.creer_locataire(
            self.autre_chambre,
            "Locataire B",
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

    @staticmethod
    def creer_locataire(chambre, nom):
        return Locataire.objects.create(
            nom_complet=nom,
            chambre=chambre,
            date_entree=date.today(),
            kwh_entree=Decimal("0"),
        )

    def test_legacy_entry_payment_rejects_another_owners_tenant(self):
        response = self.client.post(
            reverse("paiements:entree"),
            {
                "locataire": self.autre_locataire.pk,
                "montant_paye": "50000",
                "reste": "0",
                "date_paiement": date.today().isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Paiement.objects.exists())

    def test_monthly_payment_rejects_another_owners_tenant(self):
        response = self.client.post(
            reverse("paiements:mensuel"),
            {
                "locataire": self.autre_locataire.pk,
                "montant_paye": "50000",
                "reste": "0",
                "mois": str(date.today().month),
                "annee": str(date.today().year),
                "date_paiement": date.today().isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Paiement.objects.exists())

    def test_monthly_payment_accepts_the_current_owners_tenant(self):
        response = self.client.post(
            reverse("paiements:mensuel"),
            {
                "locataire": self.locataire.pk,
                "montant_paye": "50000",
                "reste": "0",
                "mois": str(date.today().month),
                "annee": str(date.today().year),
                "date_paiement": date.today().isoformat(),
            },
        )

        self.assertRedirects(response, reverse("paiements:liste"))
        self.assertEqual(Paiement.objects.get().locataire, self.locataire)

    def test_monthly_payment_get_does_not_load_another_owners_tenant(self):
        response = self.client.get(
            reverse("paiements:mensuel"),
            {"locataire": self.autre_locataire.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["locataire"])
        self.assertQuerySetEqual(
            response.context["form"].fields["locataire"].queryset,
            [self.locataire],
        )

    def test_exit_payment_rejects_another_owners_tenant(self):
        response = self.client.post(
            reverse("paiements:sortie"),
            {
                "locataire": self.autre_locataire.pk,
                "date_sortie": date.today().isoformat(),
                "kwh_sortie": "0",
                "prix_kwh": "0",
                "montant_facture_eau": "0",
                "montant_dommages": "0",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Paiement.objects.exists())

    def test_partial_first_month_payment_does_not_activate_tenant(self):
        locataire = Locataire.objects.create(
            nom_complet="Locataire en attente",
            chambre=self.chambre,
            date_entree=date.today(),
            kwh_entree=Decimal("0"),
            statut=StatutLocataire.EN_ATTENTE,
        )

        response = self.client.post(
            reverse(
                "paiements:premier_mois_entree",
                kwargs={"locataire_id": locataire.pk},
            ),
            {
                "montant_paye": "25000",
                "date_paiement": date.today().isoformat(),
                "confirmer_paiement": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        locataire.refresh_from_db()
        self.chambre.refresh_from_db()
        self.assertEqual(locataire.statut, StatutLocataire.EN_ATTENTE)
        self.assertEqual(self.chambre.statut, "LIBRE")
        self.assertFalse(
            Paiement.objects.filter(locataire=locataire, type=TypePaiement.ENTREE).exists()
        )
        self.assertIn("montant_paye", response.context["form"].errors)

    def test_exit_receipt_uses_the_confirmed_calculation_snapshot(self):
        self.chambre.caution_eau = Decimal("300")
        self.chambre.caution_electricite = Decimal("500")
        self.chambre.save()
        self.chambre.statut = "OCCUPEE"
        self.chambre.save()
        self.locataire.kwh_entree = Decimal("100")
        self.locataire.caution_eau = Decimal("300")
        self.locataire.caution_electricite = Decimal("500")
        self.locataire.avance_loyer = Decimal("10000")
        self.locataire.save()

        response = self.client.post(
            reverse(
                "paiements:sortie_locataire",
                kwargs={"locataire_id": self.locataire.pk},
            ),
            {
                "locataire": self.locataire.pk,
                "date_sortie": date.today().isoformat(),
                "kwh_sortie": "90",
                "prix_kwh": "100",
                "montant_facture_eau": "400",
                "description_dommages": "Serrure abîmée",
                "montant_dommages": "900",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "paiements/paiement_sortie_confirmation.html")

        response = self.client.post(reverse("paiements:sortie_confirmer"))

        self.assertRedirects(
            response,
            reverse("paiements:sortie_pdf", kwargs={"locataire_id": self.locataire.pk}),
        )
        paiement = Paiement.objects.get(
            locataire=self.locataire,
            type=TypePaiement.SORTIE,
        )
        resultat_enregistre = paiement.details_sortie["resultat"]
        self.assertEqual(resultat_enregistre["eau"]["montant_facture"], "400")
        self.assertEqual(resultat_enregistre["electricite"]["montant_difference"], "1000.00")
        self.assertEqual(resultat_enregistre["dommages"]["description"], "Serrure abîmée")
        self.assertEqual(resultat_enregistre["dommages"]["montant"], "900")
        self.assertEqual(resultat_enregistre["avance"]["montant_final"], "8500.00")

        with patch("weasyprint.HTML") as html_class:
            html_class.return_value.write_pdf.return_value = b"%PDF"
            response = self.client.get(
                reverse("paiements:sortie_pdf", kwargs={"locataire_id": self.locataire.pk})
            )

        self.assertEqual(response.status_code, 200)
        html = html_class.call_args.kwargs["string"]
        self.assertIn("400 FCFA", html)
        self.assertIn("1000 FCFA", html)
        self.assertIn("Serrure abîmée", html)
