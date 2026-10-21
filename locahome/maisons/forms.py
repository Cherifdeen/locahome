from django import forms

from .models import Maison


class MaisonForm(forms.ModelForm):
    """Formulaire pour créer/modifier une maison."""

    class Meta:
        model = Maison
        fields = ["nom", "quartier", "type_maison", "adresse", "description", "photo"]
        widgets = {
            "nom": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Ex: Résidence Les Palmiers",
            }),
            "quartier": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Ex: Cocody, Plateau...",
            }),
            "type_maison": forms.Select(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500",
            }),
            "adresse": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Adresse complète (optionnel)",
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "rows": 3,
                "placeholder": "Description de la maison...",
            }),
            "photo": forms.FileInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500",
            }),
        }
