import re
from datetime import date
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from locahome.chambres.models import Chambre

from .models import Locataire


class LocataireForm(forms.ModelForm):
    class Meta:
        model = Locataire
        fields = [
            "nom_complet",
            "telephone",
            "email",
            "adresse",
            "chambre",
            "date_entree",
            "date_sortie",
            "kwh_entree",
            "caution_eau",
            "caution_electricite",
            "avance_loyer",
            "statut",
        ]
        widgets = {
            "nom_complet": forms.TextInput(
                attrs={"class": "w-full border rounded px-3 py-2", "placeholder": "Nom complet du locataire"}
            ),
            "telephone": forms.TextInput(
                attrs={"class": "w-full border rounded px-3 py-2", "placeholder": "Téléphone (facultatif)"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "w-full border rounded px-3 py-2", "placeholder": "Email (facultatif)"}
            ),
            "adresse": forms.TextInput(
                attrs={"class": "w-full border rounded px-3 py-2", "placeholder": "Adresse (facultatif)"}
            ),
            "chambre": forms.Select(attrs={"class": "w-full border rounded px-3 py-2"}),
            "date_entree": forms.DateInput(
                attrs={"class": "w-full border rounded px-3 py-2", "type": "date"}
            ),
            "date_sortie": forms.DateInput(
                attrs={"class": "w-full border rounded px-3 py-2", "type": "date"}
            ),
            "kwh_entree": forms.NumberInput(
                attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0", "placeholder": "Index KWh à l'entrée"}
            ),
            "caution_eau": forms.NumberInput(
                attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0", "placeholder": "0"}
            ),
            "caution_electricite": forms.NumberInput(
                attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0", "placeholder": "0"}
            ),
            "avance_loyer": forms.NumberInput(
                attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0", "placeholder": "0"}
            ),
            "statut": forms.Select(attrs={"class": "w-full border rounded px-3 py-2"}),
        }

    def __init__(self, *args, proprietaire=None, **kwargs):
        super().__init__(*args, **kwargs)
        if proprietaire is None:
            self.fields["chambre"].queryset = Chambre.objects.none()
        elif not self.instance.pk:
            self.fields["chambre"].queryset = Chambre.objects.filter(
                maison__proprietaire=proprietaire,
                statut="LIBRE",
            )
        else:
            self.fields["chambre"].queryset = Chambre.objects.filter(
                maison__proprietaire=proprietaire
            )


class FormalitesEntreeForm(forms.Form):
    """Étape 1 : Formalités d'entrée (avance + caution eau)."""

    # Infos locataire
    nom_complet = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
            "placeholder": "Nom complet du locataire",
        }),
    )
    telephone = forms.CharField(
        max_length=10,
        min_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
            "placeholder": "9712345678",
            "pattern": "[0-9]{10}",
            "maxlength": "10",
        }),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
            "placeholder": "email@exemple.com",
        }),
    )

    # Date d'entrée
    date_entree = forms.DateField(
        widget=forms.DateInput(attrs={
            "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
            "type": "date",
        }),
    )

    # KWh d'entrée
    kwh_entree = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
            "step": "0.01",
            "min": "0",
            "placeholder": "Relevé du compteur",
        }),
    )

    # Nombre de clés
    nombre_cles = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
            "min": "1",
        }),
    )

    # Confirmations de paiement
    avance_payee = forms.BooleanField(
        required=True,
        label="Je confirme que l'avance a été payée",
        widget=forms.CheckboxInput(attrs={
            "class": "h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500",
        }),
    )
    caution_eau_payee = forms.BooleanField(
        required=True,
        label="Je confirme que la caution eau a été payée",
        widget=forms.CheckboxInput(attrs={
            "class": "h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500",
        }),
    )
    caution_elec_payee = forms.BooleanField(
        required=True,
        label="Je confirme que la caution électricité a été payée",
        widget=forms.CheckboxInput(attrs={
            "class": "h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500",
        }),
    )

    def clean_telephone(self):
        telephone = self.cleaned_data.get("telephone", "")
        telephone = telephone.strip()
        if not re.match(r"^\d{10}$", telephone):
            raise ValidationError("Le numéro doit contenir exactement 10 chiffres.")
        return f"+229{telephone}"


class PremierMoisForm(forms.Form):
    """Étape 2 : Paiement du premier mois."""

    montant_paye = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
            "step": "1",
            "min": "0",
        }),
    )
    date_paiement = forms.DateField(
        widget=forms.DateInput(attrs={
            "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
            "type": "date",
        }),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-indigo-500",
            "rows": 2,
            "placeholder": "Notes (facultatif)",
        }),
    )
    confirmer_paiement = forms.BooleanField(
        required=True,
        label="Je confirme avoir reçu ce paiement",
        widget=forms.CheckboxInput(attrs={
            "class": "h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500",
        }),
    )

    def __init__(self, *args, montant_attendu: Decimal, **kwargs):
        super().__init__(*args, **kwargs)
        self.montant_attendu = montant_attendu

    def clean_montant_paye(self):
        montant_paye = self.cleaned_data["montant_paye"]
        if montant_paye != self.montant_attendu:
            raise ValidationError(
                f"Le montant du premier mois doit être exactement de "
                f"{self.montant_attendu} FCFA."
            )
        return montant_paye

    def clean_date_paiement(self):
        date_paiement = self.cleaned_data.get("date_paiement")
        if date_paiement and date_paiement > date.today():
            raise ValidationError("La date de paiement ne peut pas être dans le futur.")
        return date_paiement
