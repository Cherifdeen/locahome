from django.contrib import admin

from .models import Chambre, NoteChambre


@admin.register(Chambre)
class ChambreAdmin(admin.ModelAdmin):
    list_display = ("numero", "nom", "statut", "prix_location", "cree_le")
    list_filter = ("statut",)
    search_fields = ("numero", "nom")
    ordering = ("numero",)


@admin.register(NoteChambre)
class NoteChambreAdmin(admin.ModelAdmin):
    list_display = ("chambre", "type", "statut", "titre", "cree_le")
    list_filter = ("type", "statut")
    search_fields = ("chambre__numero", "chambre__nom", "titre")

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