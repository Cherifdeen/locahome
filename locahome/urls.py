from datetime import date

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import include, path
from django.views.generic import TemplateView

from locahome.services.dashboard import get_nom_mois, get_statistiques_dashboard


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proprietaire = self.request.user.proprietaire
        
        stats = get_statistiques_dashboard(proprietaire)
        
        aujourdhui = date.today()
        
        context["stats"] = stats
        context["mois_courant"] = get_nom_mois(aujourdhui.month)
        context["annee_courante"] = aujourdhui.year
        
        return context


urlpatterns = [
    path("admin/", admin.site.urls),
    # Vitrine publique
    path("", include("locahome.vitrine.urls", namespace="vitrine")),
    # Auth
    path("compte/", include("locahome.comptes.urls", namespace="comptes")),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="vitrine:accueil"), name="logout"),
    # Dashboard protégé
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    # Maisons
    path("dashboard/maisons/", include("locahome.maisons.urls", namespace="maisons")),
    # Chambres
    path("dashboard/chambres/", include("locahome.chambres.urls", namespace="chambres")),
    # Locataires
    path("dashboard/locataires/", include("locahome.locataires.urls", namespace="locataires")),
    # Paiements
    path("dashboard/paiements/", include("locahome.paiements.urls", namespace="paiements")),
    # Paramètres
    path("dashboard/parametres/", include("locahome.parametres.urls", namespace="parametres")),
]



