from django.contrib import admin

from .models import ParametresProprietaire


@admin.register(ParametresProprietaire)
class ParametresProprietaireAdmin(admin.ModelAdmin):
    list_display = ("proprietaire", "prix_kwh", "prix_location_defaut", "nombre_mois_avance", "montant_caution_eau")
