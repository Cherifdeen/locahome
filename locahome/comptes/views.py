from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.views.generic import CreateView

from .forms import InscriptionProprietaireForm


class InscriptionView(CreateView):
    """Vue d'inscription pour les nouveaux propriétaires."""

    form_class = InscriptionProprietaireForm
    template_name = "registration/inscription.html"

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f"Bienvenue {user.proprietaire.nom_complet} ! Votre compte a été créé.")
        return redirect("dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)
