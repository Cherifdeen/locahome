from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from .defaults import get_defaults_parametres
from .forms import ParametresForm
from .models import ParametresProprietaire


class ParametresUpdateView(LoginRequiredMixin, UpdateView):
    """Modifier les paramètres du propriétaire."""

    model = ParametresProprietaire
    form_class = ParametresForm
    template_name = "parametres/parametres_form.html"
    success_url = reverse_lazy("parametres:modifier")

    def get_object(self, queryset=None):
        parametres, created = ParametresProprietaire.objects.get_or_create(
            proprietaire=self.request.user.proprietaire,
            defaults=get_defaults_parametres(),
        )
        return parametres

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["defaults"] = get_defaults_parametres()
        return context

    def form_valid(self, form):
        messages.success(self.request, "Paramètres enregistrés avec succès.")
        return super().form_valid(form)
