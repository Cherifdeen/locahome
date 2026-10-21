from django import forms

from .models import ParametresProprietaire


class ParametresForm(forms.ModelForm):
    """Formulaire pour les paramètres du propriétaire."""

    class Meta:
        model = ParametresProprietaire
        fields = [
            "nombre_mois_avance",
            "montant_caution_eau",
            "prix_kwh",
            "prix_location_defaut",
            "texte_legal_entree",
            "texte_legal_mensuel",
            "texte_legal_sortie",
            "logo",
            "signature",
        ]
        widgets = {
            "nombre_mois_avance": forms.NumberInput(attrs={
                "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
                "min": "1",
            }),
            "montant_caution_eau": forms.NumberInput(attrs={
                "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
                "min": "0",
                "step": "1",
            }),
            "prix_kwh": forms.NumberInput(attrs={
                "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
                "min": "0",
                "step": "0.01",
            }),
            "prix_location_defaut": forms.NumberInput(attrs={
                "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
                "min": "0",
                "step": "1",
            }),
            "texte_legal_entree": forms.Textarea(attrs={
                "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
                "rows": 3,
            }),
            "texte_legal_mensuel": forms.Textarea(attrs={
                "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
                "rows": 3,
            }),
            "texte_legal_sortie": forms.Textarea(attrs={
                "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
                "rows": 3,
            }),
        }
        labels = {
            "nombre_mois_avance": "Nombre de mois d'avance",
            "montant_caution_eau": "Montant caution eau (FCFA)",
            "prix_kwh": "Prix du KWh (FCFA)",
            "prix_location_defaut": "Prix de location par défaut (FCFA)",
            "texte_legal_entree": "Texte légal - Reçu d'entrée",
            "texte_legal_mensuel": "Texte légal - Reçu mensuel",
            "texte_legal_sortie": "Texte légal - Reçu de sortie",
            "logo": "Logo (pour les PDF)",
            "signature": "Signature (pour les PDF)",
        }
