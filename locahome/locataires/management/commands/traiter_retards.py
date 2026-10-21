"""
Commande pour traiter les retards de paiement et effectuer les soustractions sur l'avance.

Usage:
    python manage.py traiter_retards              # Traiter tous les locataires
    python manage.py traiter_retards --dry-run    # Simulation sans modification
    python manage.py traiter_retards --locataire 5  # Traiter un locataire spécifique
"""

from django.core.management.base import BaseCommand

from locahome.locataires.models import Locataire
from locahome.services.paiements import traiter_retards_locataire, get_mois_impayes


class Command(BaseCommand):
    help = "Traite les retards de paiement et effectue les soustractions sur l'avance"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulation : affiche les retards sans effectuer les soustractions",
        )
        parser.add_argument(
            "--locataire",
            type=int,
            help="ID du locataire à traiter (optionnel)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        locataire_id = options.get("locataire")

        if locataire_id:
            locataires = Locataire.objects.filter(pk=locataire_id, statut="EN_COURS")
        else:
            locataires = Locataire.objects.filter(statut="EN_COURS")

        if not locataires.exists():
            self.stdout.write(self.style.WARNING("Aucun locataire en cours trouvé."))
            return

        total_soustractions = 0

        for locataire in locataires:
            self.stdout.write(f"\n{'='*50}")
            self.stdout.write(f"Locataire: {locataire.nom_complet}")
            self.stdout.write(f"Chambre: {locataire.chambre.numero}")
            self.stdout.write(f"Date d'entrée: {locataire.date_entree}")
            self.stdout.write(f"Avance actuelle: {locataire.avance_loyer} FCFA")

            impayes = get_mois_impayes(locataire)
            
            if not impayes:
                self.stdout.write(self.style.SUCCESS("  ✓ Aucun retard"))
                continue

            self.stdout.write(self.style.WARNING(f"  ⚠ {len(impayes)} mois impayé(s):"))
            for impaye in impayes:
                self.stdout.write(f"    - {impaye['mois']} (période {impaye['periode']})")

            if dry_run:
                self.stdout.write(self.style.NOTICE("  [DRY-RUN] Pas de soustraction effectuée"))
            else:
                resultats = traiter_retards_locataire(locataire)
                if resultats:
                    for res in resultats:
                        self.stdout.write(
                            self.style.ERROR(f"  → Soustrait {res['montant']} FCFA pour {res['mois']}")
                        )
                        total_soustractions += 1
                    locataire.refresh_from_db()
                    self.stdout.write(f"  Nouvelle avance: {locataire.avance_loyer} FCFA")
                else:
                    self.stdout.write("  (Déjà traité précédemment)")

        self.stdout.write(f"\n{'='*50}")
        if dry_run:
            self.stdout.write(self.style.NOTICE("Mode simulation - Aucune modification effectuée"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Terminé ! {total_soustractions} soustraction(s) effectuée(s)"))
