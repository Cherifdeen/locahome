from django.contrib import admin

from .models import Maison


@admin.register(Maison)
class MaisonAdmin(admin.ModelAdmin):
    list_display = ("nom", "quartier", "type_maison", "proprietaire", "nombre_chambres_total", "nombre_chambres_libres")
    list_filter = ("type_maison", "quartier")
    search_fields = ("nom", "quartier", "adresse", "proprietaire__nom_complet")
