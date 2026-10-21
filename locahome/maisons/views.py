from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import MaisonForm
from .models import Maison


class MaisonListView(LoginRequiredMixin, ListView):
    """Liste des maisons du propriétaire connecté."""

    model = Maison
    template_name = "maisons/maison_list.html"
    context_object_name = "maisons"

    def get_queryset(self):
        return Maison.objects.filter(proprietaire=self.request.user.proprietaire)


class MaisonDetailView(LoginRequiredMixin, DetailView):
    """Détail d'une maison avec ses chambres."""

    model = Maison
    template_name = "maisons/maison_detail.html"
    context_object_name = "maison"

    def get_queryset(self):
        return Maison.objects.filter(proprietaire=self.request.user.proprietaire)


class MaisonCreateView(LoginRequiredMixin, CreateView):
    """Créer une nouvelle maison."""

    model = Maison
    form_class = MaisonForm
    template_name = "maisons/maison_form.html"

    def form_valid(self, form):
        form.instance.proprietaire = self.request.user.proprietaire
        messages.success(self.request, f"Maison '{form.instance.nom}' créée avec succès.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("maisons:liste")


class MaisonUpdateView(LoginRequiredMixin, UpdateView):
    """Modifier une maison."""

    model = Maison
    form_class = MaisonForm
    template_name = "maisons/maison_form.html"

    def get_queryset(self):
        return Maison.objects.filter(proprietaire=self.request.user.proprietaire)

    def form_valid(self, form):
        messages.success(self.request, f"Maison '{form.instance.nom}' modifiée avec succès.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("maisons:detail", kwargs={"pk": self.object.pk})


class MaisonDeleteView(LoginRequiredMixin, DeleteView):
    """Supprimer une maison."""

    model = Maison
    template_name = "maisons/maison_confirm_delete.html"
    success_url = reverse_lazy("maisons:liste")

    def get_queryset(self):
        return Maison.objects.filter(proprietaire=self.request.user.proprietaire)

    def form_valid(self, form):
        messages.success(self.request, f"Maison '{self.object.nom}' supprimée.")
        return super().form_valid(form)
