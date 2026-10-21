from django.contrib import admin

from .models import Proprietaire


@admin.register(Proprietaire)
class ProprietaireAdmin(admin.ModelAdmin):
    list_display = ("nom_complet", "telephone", "user", "cree_le")
    search_fields = ("nom_complet", "telephone", "user__username")
