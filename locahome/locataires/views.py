from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from locahome.chambres.models import Chambre
from locahome.paiements.models import Paiement, TypePaiement

from .forms import FormalitesEntreeForm, LocataireForm, PremierMoisForm
from .models import Locataire


NOMS_MOIS = [
    "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]


class LocataireListView(LoginRequiredMixin, ListView):
    model = Locataire
    template_name = "locataires/locataire_list.html"
    context_object_name = "locataires"

    def get_queryset(self):
        queryset = Locataire.objects.filter(
            chambre__maison__proprietaire=self.request.user.proprietaire
        ).select_related("chambre", "chambre__maison")
        
        statut = self.request.GET.get("statut")
        if statut:
            queryset = queryset.filter(statut=statut)
        
        chambre_id = self.request.GET.get("chambre")
        if chambre_id:
            try:
                queryset = queryset.filter(chambre_id=int(chambre_id))
            except (ValueError, TypeError):
                pass
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chambres"] = Chambre.objects.filter(
            maison__proprietaire=self.request.user.proprietaire
        )
        context["statut_filtre"] = self.request.GET.get("statut", "")
        context["chambre_filtre"] = self.request.GET.get("chambre", "")
        
        for locataire in context["locataires"]:
            try:
                if locataire.date_entree <= date.today() and locataire.statut == "EN_COURS":
                    locataire.en_retard = locataire.est_actuellement_en_retard()
                else:
                    locataire.en_retard = False
            except ValueError:
                locataire.en_retard = False
        
        return context


class LocataireDetailView(LoginRequiredMixin, DetailView):
    model = Locataire
    template_name = "locataires/locataire_detail.html"
    context_object_name = "locataire"

    def get_queryset(self):
        return Locataire.objects.filter(
            chambre__maison__proprietaire=self.request.user.proprietaire
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        locataire = self.object
        context["paiements"] = locataire.paiements.order_by("-date_paiement")
        context["consommation_kwh"] = getattr(locataire, "consommation_kwh", None)
        
        try:
            if locataire.date_entree <= date.today() and locataire.statut == "EN_COURS":
                context["en_retard"] = locataire.est_actuellement_en_retard()
            else:
                context["en_retard"] = False
        except ValueError:
            context["en_retard"] = False
        
        return context


class LocataireUpdateView(LoginRequiredMixin, UpdateView):
    model = Locataire
    form_class = LocataireForm
    template_name = "locataires/locataire_form.html"

    def get_queryset(self):
        return Locataire.objects.filter(
            chambre__maison__proprietaire=self.request.user.proprietaire
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["proprietaire"] = self.request.user.proprietaire
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Locataire {form.cleaned_data['nom_complet']} modifié avec succès.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class FormalitesEntreeView(LoginRequiredMixin, View):
    """Étape 1 : Formalités d'entrée pour une chambre."""

    template_name = "locataires/formalites_entree.html"

    def get_chambre(self):
        chambre_id = self.kwargs.get("chambre_id")
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
        chambre = self.get_chambre()
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
        chambre = self.get_chambre()
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
            return redirect("locataires:premier_mois", locataire_id=locataire.pk)
        
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


class PremierMoisView(LoginRequiredMixin, View):
    """Étape 2 : Paiement du premier mois."""

    template_name = "locataires/premier_mois.html"

    def get_locataire(self):
        locataire_id = self.kwargs.get("locataire_id")
        return get_object_or_404(
            Locataire,
            pk=locataire_id,
            chambre__maison__proprietaire=self.request.user.proprietaire,
            statut="EN_ATTENTE",
        )

    def get(self, request, locataire_id):
        locataire = self.get_locataire()
        
        # Vérifier si le premier mois a déjà été payé
        if Paiement.objects.filter(locataire=locataire, type=TypePaiement.ENTREE).exists():
            messages.info(request, "Le premier mois a déjà été payé.")
            return redirect("locataires:detail", pk=locataire.pk)
        
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
        locataire = self.get_locataire()
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
            return redirect("locataires:detail", pk=locataire.pk)
        
        context = {
            "form": form,
            "locataire": locataire,
            "montant_attendu": locataire.chambre.prix_location,
        }
        return render(request, self.template_name, context)


class FormalitesPDFView(LoginRequiredMixin, View):
    """Génère le PDF du reçu de formalités d'entrée."""
    
    def get(self, request, locataire_id):
        from weasyprint import HTML
        
        locataire = get_object_or_404(
            Locataire,
            pk=locataire_id,
            chambre__maison__proprietaire=request.user.proprietaire,
        )
        
        paiement = Paiement.objects.filter(
            locataire=locataire,
            type=TypePaiement.FORMALITES,
        ).first()
        
        if not paiement:
            messages.error(request, "Aucun paiement de formalités trouvé.")
            return redirect("locataires:detail", pk=locataire.pk)
        
        try:
            parametres = request.user.proprietaire.parametres
        except:
            parametres = None
        
        chambre = locataire.chambre
        nombre_mois_avance = parametres.nombre_mois_avance if parametres else 3
        montant_avance = chambre.prix_location * nombre_mois_avance
        
        context = {
            "locataire": locataire,
            "chambre": chambre,
            "paiement": paiement,
            "parametres": parametres,
            "nombre_mois_avance": nombre_mois_avance,
            "montant_avance": montant_avance,
            "date_generation": date.today(),
        }
        
        html_string = render_to_string("locataires/pdf/formalites.html", context, request=request)
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type="application/pdf")
        filename = f"formalites_{locataire.nom_complet.replace(' ', '_')}_{date.today()}.pdf"
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        
        return response


class PremierMoisPDFView(LoginRequiredMixin, View):
    """Génère le PDF du reçu du premier mois."""
    
    def get(self, request, locataire_id):
        from weasyprint import HTML
        
        locataire = get_object_or_404(
            Locataire,
            pk=locataire_id,
            chambre__maison__proprietaire=request.user.proprietaire,
        )
        
        paiement = Paiement.objects.filter(
            locataire=locataire,
            type=TypePaiement.ENTREE,
        ).first()
        
        if not paiement:
            messages.error(request, "Aucun paiement du premier mois trouvé.")
            return redirect("locataires:detail", pk=locataire.pk)
        
        try:
            parametres = request.user.proprietaire.parametres
        except:
            parametres = None
        
        chambre = locataire.chambre
        
        paiement_formalites = Paiement.objects.filter(
            locataire=locataire,
            type=TypePaiement.FORMALITES,
        ).first()
        
        total_formalites = paiement_formalites.montant_paye if paiement_formalites else Decimal("0")
        total_entree = total_formalites + paiement.montant_paye
        
        context = {
            "locataire": locataire,
            "chambre": chambre,
            "paiement": paiement,
            "parametres": parametres,
            "nom_mois": NOMS_MOIS[paiement.mois] if paiement.mois else "",
            "total_entree": total_entree,
            "date_generation": date.today(),
        }
        
        html_string = render_to_string("locataires/pdf/premier_mois.html", context, request=request)
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type="application/pdf")
        filename = f"premier_mois_{locataire.nom_complet.replace(' ', '_')}_{date.today()}.pdf"
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        
        return response
