from django.contrib import admin

from .models import Locataire


@admin.register(Locataire)
class LocataireAdmin(admin.ModelAdmin):
    list_display = (
        "nom_complet",
        "chambre",
        "date_entree",
        "date_sortie",
        "statut",
        "avance_loyer",
    )
    list_filter = ("statut", "chambre")
    search_fields = ("nom_complet", "chambre__numero", "chambre__nom")
    date_hierarchy = "date_entree"

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