from dataclasses import fields, is_dataclass
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, ListView

from locahome.chambres.models import Chambre
from locahome.locataires.models import Locataire
from locahome.parametres.models import ParametresProprietaire
from locahome.services.avance import get_avance_en_mois, get_niveau_alerte
from locahome.services.paiements import get_mois_impayes

from .forms import PaiementEntreeForm, PaiementMensuelForm, PaiementSortieForm
from .models import ConsommationKwh, Paiement, TypePaiement

CHAMPS_MONTANTS_SORTIE = {
    "montant_initial",
    "defalcation_loyers_impayes",
    "defalcation_electricite",
    "defalcation_eau",
    "defalcation_dommages",
    "montant_final",
    "kwh_entree",
    "kwh_sortie",
    "difference_kwh",
    "prix_kwh",
    "montant_difference",
    "montant_a_payer",
    "caution_initiale",
    "du_au_locataire",
    "a_payer_par_locataire",
    "defalque_sur_avance",
    "montant_facture",
    "solde",
    "montant",
    "total_du_au_locataire",
    "total_a_payer_par_locataire",
    "solde_final",
}


def _valeur_json_sortie(valeur):
    if isinstance(valeur, Decimal):
        return str(valeur)
    if is_dataclass(valeur):
        return {
            champ.name: _valeur_json_sortie(getattr(valeur, champ.name))
            for champ in fields(valeur)
        }
    if isinstance(valeur, dict):
        return {cle: _valeur_json_sortie(element) for cle, element in valeur.items()}
    if isinstance(valeur, (list, tuple)):
        return [_valeur_json_sortie(element) for element in valeur]
    return valeur


def _valeur_sortie_pour_template(valeur, cle=None):
    if isinstance(valeur, dict):
        return {
            cle_enfant: _valeur_sortie_pour_template(valeur_enfant, cle_enfant)
            for cle_enfant, valeur_enfant in valeur.items()
        }
    if cle in CHAMPS_MONTANTS_SORTIE and isinstance(valeur, str):
        return Decimal(valeur)
    return valeur


class PaiementListView(LoginRequiredMixin, ListView):
    model = Paiement
    template_name = "paiements/paiement_list.html"
    context_object_name = "paiements"

    def get_queryset(self):
        proprietaire = self.request.user.proprietaire
        queryset = Paiement.objects.filter(
            locataire__chambre__maison__proprietaire=proprietaire
        ).select_related("locataire", "locataire__chambre").order_by("-date_paiement")
        
        # Filtre par locataire
        locataire_id = self.request.GET.get("locataire")
        if locataire_id:
            try:
                queryset = queryset.filter(locataire_id=int(locataire_id))
            except (ValueError, TypeError):
                pass
        # Filtre par type
        type_paiement = self.request.GET.get("type")
        if type_paiement:
            queryset = queryset.filter(type=type_paiement)
        # Filtre par année
        annee = self.request.GET.get("annee")
        if annee:
            try:
                queryset = queryset.filter(annee=int(annee))
            except (ValueError, TypeError):
                pass
        # Filtre par mois
        mois = self.request.GET.get("mois")
        if mois:
            try:
                queryset = queryset.filter(mois=int(mois))
            except (ValueError, TypeError):
                pass
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proprietaire = self.request.user.proprietaire

        context["locataires"] = Locataire.objects.filter(
            chambre__maison__proprietaire=proprietaire,
            statut="EN_COURS"
        ).order_by("nom_complet")
        context["locataire_filtre"] = self.request.GET.get("locataire", "")
        context["type_filtre"] = self.request.GET.get("type", "")
        context["annee_filtre"] = self.request.GET.get("annee", "")
        context["mois_filtre"] = self.request.GET.get("mois", "")
        # Années disponibles pour le filtre
        context["annees"] = (
            Paiement.objects.filter(
                locataire__chambre__maison__proprietaire=proprietaire
            ).exclude(annee__isnull=True).values_list("annee", flat=True).distinct().order_by("-annee")
        )
        # Liste des mois
        context["mois_liste"] = [
            (1, "Janvier"), (2, "Février"), (3, "Mars"), (4, "Avril"),
            (5, "Mai"), (6, "Juin"), (7, "Juillet"), (8, "Août"),
            (9, "Septembre"), (10, "Octobre"), (11, "Novembre"), (12, "Décembre"),
        ]
        # Dictionnaire pour les noms de mois
        context["mois_dict"] = {
            1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
            5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
            9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
        }
        return context


class PaiementEntreeAvecLocataireView(LoginRequiredMixin, View):
    """Nouveau flux : création locataire + formalités + premier mois en un seul place."""
    
    template_name = "paiements/paiement_entree_avec_locataire.html"
    
    def get_chambre(self, chambre_id):
        return get_object_or_404(
            Chambre,
            pk=chambre_id,
            maison__proprietaire=self.request.user.proprietaire,
            statut="LIBRE",
        )
    
    def get_parametres(self):
        try:
            return self.request.user.proprietaire.parametres
        except:
            return None
    
    def get(self, request, chambre_id):
        from locahome.locataires.forms import FormalitesEntreeForm
        chambre = self.get_chambre(chambre_id)
        parametres = self.get_parametres()
        
        if not parametres:
            messages.error(request, "Veuillez d'abord configurer vos paramètres (nombre de mois d'avance, etc.)")
            return redirect("parametres:modifier")
        
        form = FormalitesEntreeForm()
        montant_avance = chambre.prix_location * parametres.nombre_mois_avance
        
        context = {
            "form": form,
            "chambre": chambre,
            "parametres": parametres,
            "montant_avance": montant_avance,
            "caution_eau": chambre.caution_eau,
            "caution_electricite": chambre.caution_electricite,
            "total_formalites": montant_avance + chambre.caution_eau + chambre.caution_electricite,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, chambre_id):
        from locahome.locataires.forms import FormalitesEntreeForm
        from locahome.locataires.models import Locataire
        
        chambre = self.get_chambre(chambre_id)
        parametres = self.get_parametres()
        form = FormalitesEntreeForm(request.POST)
        
        if form.is_valid():
            montant_avance = chambre.prix_location * parametres.nombre_mois_avance
            total_formalites = montant_avance + chambre.caution_eau + chambre.caution_electricite
            
            # Créer le locataire (en attente jusqu'au paiement du premier mois)
            locataire = Locataire.objects.create(
                nom_complet=form.cleaned_data["nom_complet"],
                telephone=form.cleaned_data["telephone"],
                email=form.cleaned_data.get("email", ""),
                chambre=chambre,
                date_entree=form.cleaned_data["date_entree"],
                kwh_entree=form.cleaned_data["kwh_entree"],
                nombre_cles=form.cleaned_data["nombre_cles"],
                avance_initiale=montant_avance,
                avance_loyer=montant_avance,
                caution_eau=chambre.caution_eau,
                caution_electricite=chambre.caution_electricite,
                statut="EN_ATTENTE",
            )
            
            # Créer le paiement des formalités
            Paiement.objects.create(
                locataire=locataire,
                type=TypePaiement.FORMALITES,
                montant_paye=total_formalites,
                reste=Decimal("0"),
                date_paiement=form.cleaned_data["date_entree"],
            )
            
            messages.success(request, f"Formalités enregistrées pour {locataire.nom_complet}. Passons au paiement du premier mois.")
            return redirect("paiements:premier_mois_entree", locataire_id=locataire.pk)
        
        montant_avance = chambre.prix_location * parametres.nombre_mois_avance
        context = {
            "form": form,
            "chambre": chambre,
            "parametres": parametres,
            "montant_avance": montant_avance,
            "caution_eau": chambre.caution_eau,
            "caution_electricite": chambre.caution_electricite,
            "total_formalites": montant_avance + chambre.caution_eau + chambre.caution_electricite,
        }
        return render(request, self.template_name, context)


class PremierMoisEntreeView(LoginRequiredMixin, View):
    """Paiement du premier mois après enregistrement des formalités."""
    
    template_name = "paiements/premier_mois_entree.html"
    
    def get_locataire(self, locataire_id):
        from locahome.locataires.models import Locataire
        return get_object_or_404(
            Locataire,
            pk=locataire_id,
            chambre__maison__proprietaire=self.request.user.proprietaire,
            statut="EN_ATTENTE",
        )
    
    def get(self, request, locataire_id):
        from locahome.locataires.forms import PremierMoisForm
        locataire = self.get_locataire(locataire_id)
        
        form = PremierMoisForm(
            montant_attendu=locataire.chambre.prix_location,
            initial={
                "montant_paye": locataire.chambre.prix_location,
                "date_paiement": date.today(),
            },
        )
        
        context = {
            "form": form,
            "locataire": locataire,
            "montant_attendu": locataire.chambre.prix_location,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, locataire_id):
        from locahome.locataires.forms import PremierMoisForm
        from locahome.locataires.models import Locataire
        
        locataire = self.get_locataire(locataire_id)
        form = PremierMoisForm(
            request.POST,
            montant_attendu=locataire.chambre.prix_location,
        )
        
        if form.is_valid():
            montant_paye = form.cleaned_data["montant_paye"]
            prix_chambre = locataire.chambre.prix_location
            reste = Decimal("0")
            
            # Créer le paiement du premier mois
            Paiement.objects.create(
                locataire=locataire,
                type=TypePaiement.ENTREE,
                montant_paye=montant_paye,
                reste=reste,
                mois=locataire.date_entree.month,
                annee=locataire.date_entree.year,
                date_paiement=form.cleaned_data["date_paiement"],
            )
            
            # Mettre le locataire en cours et la chambre en OCCUPEE
            locataire.statut = "EN_COURS"
            locataire.save()
            
            chambre = locataire.chambre
            chambre.statut = "OCCUPEE"
            chambre.save()
            
            messages.success(
                request,
                f"✅ Entrée complète ! {locataire.nom_complet} occupe maintenant la chambre {chambre.numero}."
            )
            return redirect("paiements:liste")
        
        context = {
            "form": form,
            "locataire": locataire,
            "montant_attendu": locataire.chambre.prix_location,
        }
        return render(request, self.template_name, context)


class PaiementEntreeCreateView(LoginRequiredMixin, CreateView):
    """Ancienne vue - kept for backward compatibility."""
    model = Paiement
    form_class = PaiementEntreeForm
    template_name = "paiements/paiement_entree_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["proprietaire"] = self.request.user.proprietaire
        return kwargs

    def form_valid(self, form):
        paiement = form.save(commit=False)
        paiement.type = TypePaiement.ENTREE
        paiement.save()
        messages.success(self.request, f"Paiement d'entrée enregistré pour {paiement.locataire.nom_complet}.")
        return redirect("paiements:liste")


class PaiementMensuelCreateView(LoginRequiredMixin, View):
    """Vue améliorée pour le paiement mensuel avec infos retard et avance."""
    
    template_name = "paiements/paiement_mensuel_form.html"

    def get_context(self, form, locataire=None):
        context = {
            "form": form,
            "locataire": locataire,
        }
        
        if locataire:
            context["mois_impayes"] = get_mois_impayes(locataire)
            context["avance_mois"] = round(get_avance_en_mois(locataire), 1)
            context["avance_montant"] = locataire.avance_loyer
            context["niveau_alerte"] = get_niveau_alerte(locataire)
            context["prix_chambre"] = locataire.chambre.prix_location
        
        return context

    def get(self, request):
        proprietaire = request.user.proprietaire
        form = PaiementMensuelForm(proprietaire=proprietaire)
        locataire_id = request.GET.get("locataire")
        locataire = None
        
        if locataire_id:
            try:
                locataire = Locataire.objects.get(
                    pk=locataire_id,
                    chambre__maison__proprietaire=proprietaire,
                    statut="EN_COURS",
                )
                form = PaiementMensuelForm(
                    proprietaire=proprietaire,
                    initial={
                        "locataire": locataire,
                        "montant_paye": locataire.chambre.prix_location,
                    },
                )
            except Locataire.DoesNotExist:
                pass
        
        return render(request, self.template_name, self.get_context(form, locataire))

    def post(self, request):
        form = PaiementMensuelForm(
            request.POST,
            proprietaire=request.user.proprietaire,
        )
        locataire = None
        
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.type = TypePaiement.MENSUEL
            paiement.save()
            messages.success(request, f"Paiement mensuel enregistré pour {paiement.locataire.nom_complet}.")
            return redirect("paiements:liste")
        else:
            # Debug: afficher les erreurs
            if form.errors:
                messages.error(request, f"Erreurs du formulaire: {form.errors}")
        
        locataire_id = request.POST.get("locataire")
        if locataire_id:
            try:
                locataire = Locataire.objects.get(
                    pk=locataire_id,
                    chambre__maison__proprietaire=request.user.proprietaire,
                    statut="EN_COURS",
                )
            except Locataire.DoesNotExist:
                pass
        
        return render(request, self.template_name, self.get_context(form, locataire))


class PaiementSortieView(LoginRequiredMixin, View):
    """Vue de sortie avec calcul du solde final."""
    
    template_name = "paiements/paiement_sortie_form.html"

    def get_locataire(self, locataire_id):
        if not locataire_id:
            return None
        try:
            return Locataire.objects.get(
                pk=locataire_id,
                chambre__maison__proprietaire=self.request.user.proprietaire,
                statut="EN_COURS",
            )
        except Locataire.DoesNotExist:
            return None

    def get_context(self, form, locataire=None, resultat=None):
        from locahome.chambres.models import TypeDecompteur
        
        context = {
            "form": form,
            "locataire": locataire,
            "resultat": resultat,
        }
        
        if locataire:
            context["type_decompteur"] = locataire.chambre.type_decompteur
            context["is_carte"] = locataire.chambre.type_decompteur == TypeDecompteur.CARTE
            context["kwh_entree"] = locataire.kwh_entree
            context["caution_eau"] = locataire.caution_eau
            context["caution_electricite"] = locataire.caution_electricite
            context["avance_loyer"] = locataire.avance_loyer
            
            # Calculer les mois impayés
            from locahome.services.paiements import get_mois_impayes
            mois_impayes = get_mois_impayes(locataire)
            context["mois_impayes"] = mois_impayes
            context["montant_impayes"] = len(mois_impayes) * locataire.chambre.prix_location
        
        return context

    def get(self, request, locataire_id=None):
        locataire = self.get_locataire(locataire_id or request.GET.get("locataire"))
        form = PaiementSortieForm(
            locataire=locataire,
            proprietaire=request.user.proprietaire,
        )
        return render(request, self.template_name, self.get_context(form, locataire))

    def post(self, request, locataire_id=None):
        from locahome.chambres.models import TypeDecompteur
        from locahome.services.sortie import calculer_sortie
        from locahome.services.paiements import get_mois_impayes
        
        locataire = self.get_locataire(locataire_id or request.POST.get("locataire"))
        form = PaiementSortieForm(
            request.POST,
            locataire=locataire,
            proprietaire=request.user.proprietaire,
        )
        
        if form.is_valid():
            locataire = form.cleaned_data["locataire"]
            date_sortie = form.cleaned_data["date_sortie"]
            
            # Calculer les mois impayés
            mois_impayes = get_mois_impayes(locataire)
            montant_impayes = len(mois_impayes) * locataire.chambre.prix_location
            
            # Préparer les arguments selon le type de décompteur
            kwargs = {
                "montant_facture_eau": form.cleaned_data["montant_facture_eau"],
                "montant_loyers_impayes": montant_impayes,
                "description_dommages": form.cleaned_data.get("description_dommages", ""),
                "montant_dommages": form.cleaned_data.get("montant_dommages") or Decimal("0"),
            }
            
            if locataire.chambre.type_decompteur == TypeDecompteur.CARTE:
                kwargs["kwh_sortie"] = form.cleaned_data["kwh_sortie"]
                kwargs["prix_kwh"] = form.cleaned_data["prix_kwh"]
            else:
                kwargs["montant_facture_electricite"] = form.cleaned_data["montant_facture_electricite"]
            
            # Calculer le solde
            resultat = calculer_sortie(locataire, **kwargs)
            
            # Stocker en session pour la confirmation/PDF
            request.session["sortie_resultat"] = {
                "locataire_id": locataire.pk,
                "date_sortie": str(date_sortie),
                "form_data": {k: str(v) for k, v in form.cleaned_data.items() if k != "locataire"},
            }
            
            # Afficher le résumé pour confirmation
            return render(request, "paiements/paiement_sortie_confirmation.html", {
                "locataire": locataire,
                "resultat": resultat,
                "date_sortie": date_sortie,
                "mois_impayes": mois_impayes,
                "description_dommages": form.cleaned_data.get("description_dommages", ""),
                "montant_dommages": form.cleaned_data.get("montant_dommages") or Decimal("0"),
            })
        
        return render(request, self.template_name, self.get_context(form, locataire))


class ConfirmerSortieView(LoginRequiredMixin, View):
    """Confirme la sortie et génère le PDF."""
    
    def post(self, request):
        from locahome.chambres.models import TypeDecompteur
        from locahome.services.sortie import calculer_sortie
        from locahome.services.paiements import get_mois_impayes
        from decimal import Decimal
        
        sortie_data = request.session.get("sortie_resultat")
        if not sortie_data:
            messages.error(request, "Session expirée. Veuillez recommencer.")
            return redirect("paiements:sortie")
        
        try:
            locataire = Locataire.objects.get(
                pk=sortie_data["locataire_id"],
                chambre__maison__proprietaire=request.user.proprietaire,
            )
        except Locataire.DoesNotExist:
            messages.error(request, "Locataire non trouvé.")
            return redirect("paiements:sortie")
        
        form_data = sortie_data["form_data"]
        date_sortie = form_data["date_sortie"]
        
        # Recalculer et enregistrer l'instantané qui servira au reçu.
        mois_impayes = get_mois_impayes(locataire)
        montant_impayes = len(mois_impayes) * locataire.chambre.prix_location
        
        kwargs = {
            "montant_facture_eau": Decimal(form_data["montant_facture_eau"]),
            "montant_loyers_impayes": montant_impayes,
            "description_dommages": form_data.get("description_dommages", ""),
            "montant_dommages": Decimal(form_data.get("montant_dommages", "0") or "0"),
        }
        
        if locataire.chambre.type_decompteur == TypeDecompteur.CARTE:
            kwargs["kwh_sortie"] = Decimal(form_data["kwh_sortie"])
            kwargs["prix_kwh"] = Decimal(form_data["prix_kwh"])
        else:
            kwargs["montant_facture_electricite"] = Decimal(form_data["montant_facture_electricite"])
        
        resultat = calculer_sortie(locataire, **kwargs)
        
        # Créer le paiement de sortie
        solde = resultat.solde_final
        if solde >= 0:
            montant_paye = Decimal("0")
            reste = Decimal("0")
        else:
            montant_paye = abs(solde)
            reste = Decimal("0")
        
        paiement = Paiement.objects.create(
            locataire=locataire,
            type=TypePaiement.SORTIE,
            montant_paye=montant_paye,
            reste=reste,
            date_paiement=date_sortie,
            details_sortie={
                "resultat": {
                    **_valeur_json_sortie(resultat),
                    "solde_final": str(resultat.solde_final),
                },
                "form_data": form_data,
                "montant_loyers_impayes": str(montant_impayes),
            },
        )
        
        # Enregistrer la consommation KWh si décompteur à carte
        if locataire.chambre.type_decompteur == TypeDecompteur.CARTE:
            ConsommationKwh.objects.update_or_create(
                locataire=locataire,
                defaults={
                    "kwh_entree": locataire.kwh_entree,
                    "kwh_sortie": Decimal(form_data["kwh_sortie"]),
                    "consommation": abs(resultat.electricite.difference_kwh),
                    "montant_conso": resultat.electricite.montant_difference,
                    "avance": resultat.electricite.caution_initiale,
                    "dette": resultat.electricite.a_payer_par_locataire,
                    "remboursement": resultat.electricite.du_au_locataire,
                },
            )
        
        # Mettre à jour le locataire
        locataire.statut = "SORTI"
        locataire.date_sortie = date_sortie
        locataire.save()
        
        # Libérer la chambre
        chambre = locataire.chambre
        chambre.statut = "LIBRE"
        chambre.save()
        
        # Nettoyer la session
        del request.session["sortie_resultat"]
        
        # Rediriger vers le PDF
        messages.success(
            request,
            f"Sortie enregistrée pour {locataire.nom_complet}. "
            f"{'Solde dû au locataire: ' + str(resultat.total_du_au_locataire) + ' FCFA' if resultat.total_du_au_locataire > 0 else ''}"
        )
        return redirect("paiements:sortie_pdf", locataire_id=locataire.pk)


class SortiePDFView(LoginRequiredMixin, View):
    """Génère le PDF de solde final de sortie."""
    
    def get(self, request, locataire_id):
        from weasyprint import HTML
        from locahome.chambres.models import TypeDecompteur
        
        try:
            locataire = Locataire.objects.select_related(
                "chambre", "chambre__maison"
            ).get(
                pk=locataire_id,
                chambre__maison__proprietaire=request.user.proprietaire,
            )
        except Locataire.DoesNotExist:
            messages.error(request, "Locataire non trouvé.")
            return redirect("paiements:liste")
        
        # Récupérer le paiement de sortie
        paiement_sortie = Paiement.objects.filter(
            locataire=locataire,
            type=TypePaiement.SORTIE,
        ).order_by("-date_paiement").first()
        
        if not paiement_sortie:
            messages.error(request, "Aucun paiement de sortie trouvé.")
            return redirect("locataires:detail", pk=locataire.pk)

        details_sortie = paiement_sortie.details_sortie
        resultat_enregistre = details_sortie.get("resultat")
        if not resultat_enregistre:
            messages.error(
                request,
                "Ce reçu de sortie ne contient pas les détails de calcul enregistrés.",
            )
            return redirect("locataires:detail", pk=locataire.pk)
        resultat = _valeur_sortie_pour_template(resultat_enregistre)

        # Récupérer les données de consommation
        consommation = getattr(locataire, "consommation_kwh", None)
        is_carte = (
            resultat["electricite"]["type_decompteur"]
            == TypeDecompteur.CARTE
        )
        
        # Paramètres du propriétaire
        try:
            parametres = request.user.proprietaire.parametres
        except:
            parametres = None
        
        context = {
            "locataire": locataire,
            "chambre": locataire.chambre,
            "maison": locataire.chambre.maison,
            "paiement": paiement_sortie,
            "consommation": consommation,
            "resultat": resultat,
            "mois_impayes": [],
            "parametres": parametres,
            "is_carte": is_carte,
            "date_generation": date.today(),
        }
        
        # Générer le HTML
        html_string = render_to_string("paiements/pdf/sortie.html", context, request=request)
        
        # Générer le PDF
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf()
        
        # Retourner le PDF
        response = HttpResponse(pdf, content_type="application/pdf")
        filename = f"sortie_{locataire.nom_complet.replace(' ', '_')}_{date.today()}.pdf"
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        
        return response


NOMS_MOIS = [
    "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]


class MensuelPDFView(LoginRequiredMixin, View):
    """Génère le PDF du reçu de paiement mensuel."""
    
    def get(self, request, paiement_id):
        from weasyprint import HTML
        from locahome.services.avance import get_avance_en_mois
        
        paiement = get_object_or_404(
            Paiement,
            pk=paiement_id,
            type=TypePaiement.MENSUEL,
            locataire__chambre__maison__proprietaire=request.user.proprietaire,
        )
        
        locataire = paiement.locataire
        chambre = locataire.chambre
        
        try:
            parametres = request.user.proprietaire.parametres
        except:
            parametres = None
        
        context = {
            "paiement": paiement,
            "locataire": locataire,
            "chambre": chambre,
            "parametres": parametres,
            "nom_mois": NOMS_MOIS[paiement.mois] if paiement.mois else "",
            "avance_mois": round(get_avance_en_mois(locataire), 1),
            "date_generation": date.today(),
        }
        
        html_string = render_to_string("paiements/pdf/mensuel.html", context, request=request)
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type="application/pdf")
        filename = f"loyer_{locataire.nom_complet.replace(' ', '_')}_{paiement.mois}_{paiement.annee}.pdf"
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        
        return response
