from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from locahome.maisons.models import Maison

from .forms import ChambreForm
from .models import Chambre


class ChambreListView(LoginRequiredMixin, ListView):
    """Liste des chambres du propriétaire connecté."""

    model = Chambre
    template_name = "chambres/chambre_list.html"
    context_object_name = "chambres"

    def get_queryset(self):
        return Chambre.objects.filter(
            maison__proprietaire=self.request.user.proprietaire
        ).select_related("maison")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["maisons"] = self.request.user.proprietaire.maisons.all()
        return context


class ChambresLibresView(LoginRequiredMixin, ListView):
    """Liste des chambres libres pour ajouter un locataire."""

    model = Chambre
    template_name = "chambres/chambres_libres.html"
    context_object_name = "chambres"

    def get_queryset(self):
        return Chambre.objects.filter(
            maison__proprietaire=self.request.user.proprietaire,
            statut="LIBRE"
        ).select_related("maison")


class ChambreDetailView(LoginRequiredMixin, DetailView):
    """Détail d'une chambre."""

    model = Chambre
    template_name = "chambres/chambre_detail.html"
    context_object_name = "chambre"

    def get_queryset(self):
        return Chambre.objects.filter(
            maison__proprietaire=self.request.user.proprietaire
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chambre = self.object
        context["locataire_actuel"] = chambre.locataire_actuel
        context["locataires_historiques"] = chambre.locataires.order_by("-date_entree")
        context["notes"] = chambre.notes.all()
        return context


class ChambreCreateView(LoginRequiredMixin, CreateView):
    """Créer une nouvelle chambre."""

    model = Chambre
    form_class = ChambreForm
    template_name = "chambres/chambre_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["proprietaire"] = self.request.user.proprietaire
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        maison_id = self.request.GET.get("maison")
        if maison_id:
            initial["maison"] = maison_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, f"Chambre '{form.instance.numero}' créée avec succès.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("maisons:detail", kwargs={"pk": self.object.maison.pk})


class ChambreUpdateView(LoginRequiredMixin, UpdateView):
    """Modifier une chambre."""

    model = Chambre
    form_class = ChambreForm
    template_name = "chambres/chambre_form.html"

    def get_queryset(self):
        return Chambre.objects.filter(
            maison__proprietaire=self.request.user.proprietaire
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["proprietaire"] = self.request.user.proprietaire
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Chambre '{form.instance.numero}' modifiée avec succès.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("chambres:detail", kwargs={"pk": self.object.pk})


class ChambreDeleteView(LoginRequiredMixin, DeleteView):
    """Supprimer une chambre."""

    model = Chambre
    template_name = "chambres/chambre_confirm_delete.html"

    def get_queryset(self):
        return Chambre.objects.filter(
            maison__proprietaire=self.request.user.proprietaire
        )

    def get_success_url(self):
        return reverse_lazy("maisons:detail", kwargs={"pk": self.object.maison.pk})

    def form_valid(self, form):
        messages.success(self.request, f"Chambre '{self.object.numero}' supprimée.")
        return super().form_valid(form)
