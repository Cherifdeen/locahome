from django import forms

from .models import Chambre


class ChambreForm(forms.ModelForm):
    class Meta:
        model = Chambre
        fields = [
            "maison", "numero", "nom", "prix_location",
            "caution_eau", "caution_electricite", "type_decompteur",
            "description"
        ]
        widgets = {
            "maison": forms.Select(attrs={"class": "w-full border rounded px-3 py-2"}),
            "numero": forms.TextInput(
                attrs={"class": "w-full border rounded px-3 py-2", "placeholder": "Ex: 101, A1, etc."}
            ),
            "nom": forms.TextInput(
                attrs={"class": "w-full border rounded px-3 py-2", "placeholder": "Nom ou libellé (facultatif)"}
            ),
            "prix_location": forms.NumberInput(
                attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0"}
            ),
            "caution_eau": forms.NumberInput(
                attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0"}
            ),
            "caution_electricite": forms.NumberInput(
                attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0"}
            ),
            "type_decompteur": forms.Select(attrs={"class": "w-full border rounded px-3 py-2"}),
            "description": forms.Textarea(
                attrs={"class": "w-full border rounded px-3 py-2", "rows": 4, "placeholder": "Description (facultatif)"}
            ),
        }
        labels = {
            "maison": "Maison",
            "numero": "Numéro de la chambre",
            "nom": "Nom (facultatif)",
            "prix_location": "Prix de location mensuel (FCFA)",
            "caution_eau": "Caution eau (FCFA)",
            "caution_electricite": "Caution électricité (FCFA)",
            "type_decompteur": "Type de décompteur",
            "description": "Description",
        }

    def __init__(self, *args, proprietaire=None, **kwargs):
        super().__init__(*args, **kwargs)
        if proprietaire:
            self.fields["maison"].queryset = proprietaire.maisons.all()
