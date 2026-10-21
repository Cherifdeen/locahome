from django.db.models import Count, Q
from django.views.generic import DetailView, ListView

from locahome.maisons.models import Maison


class AccueilView(ListView):
    """Page d'accueil publique avec les maisons ayant des chambres libres."""

    model = Maison
    template_name = "vitrine/accueil.html"
    context_object_name = "maisons"

    def get_queryset(self):
        queryset = Maison.objects.annotate(
            chambres_libres=Count("chambres", filter=Q(chambres__statut="LIBRE"))
        ).filter(chambres_libres__gt=0)

        # Filtre par quartier
        quartier = self.request.GET.get("quartier")
        if quartier:
            queryset = queryset.filter(quartier__icontains=quartier)

        # Filtre par type de maison
        type_maison = self.request.GET.get("type")
        if type_maison:
            queryset = queryset.filter(type_maison=type_maison)

        return queryset.order_by("-cree_le")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Liste des quartiers disponibles pour le filtre
        context["quartiers"] = (
            Maison.objects.values_list("quartier", flat=True)
            .distinct()
            .order_by("quartier")
        )
        # Types de maison pour le filtre
        from locahome.maisons.models import TypeMaison
        context["types_maison"] = TypeMaison.choices
        # Filtres actifs
        context["quartier_filtre"] = self.request.GET.get("quartier", "")
        context["type_filtre"] = self.request.GET.get("type", "")
        return context


class MaisonPubliqueDetailView(DetailView):
    """Détail public d'une maison avec ses chambres libres."""

    model = Maison
    template_name = "vitrine/maison_detail.html"
    context_object_name = "maison"

    def get_queryset(self):
        return Maison.objects.annotate(
            chambres_libres=Count("chambres", filter=Q(chambres__statut="LIBRE"))
        ).filter(chambres_libres__gt=0)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chambres_disponibles"] = self.object.chambres.filter(statut="LIBRE").order_by("prix_location")
        return context
