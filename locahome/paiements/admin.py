from django.contrib import admin

from .models import ConsommationKwh, Paiement


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = (
        "locataire",
        "type",
        "montant_paye",
        "reste",
        "date_paiement",
        "mois",
        "annee",
    )
    list_filter = ("type", "annee", "mois")
    search_fields = ("locataire__nom_complet",)
    date_hierarchy = "date_paiement"


@admin.register(ConsommationKwh)
class ConsommationKwhAdmin(admin.ModelAdmin):
    list_display = (
        "locataire",
        "kwh_entree",
        "kwh_sortie",
        "consommation",
        "montant_conso",
        "avance",
        "dette",
        "remboursement",
    )
    search_fields = ("locataire__nom_complet",)

{
  "cells": [],
  "metadata": {
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 2
}