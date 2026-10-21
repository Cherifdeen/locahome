import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Proprietaire


class InscriptionProprietaireForm(UserCreationForm):
    """Formulaire d'inscription pour les propriétaires."""

    nom_complet = forms.CharField(
        max_length=150,
        label="Nom complet",
        widget=forms.TextInput(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500",
            "placeholder": "Votre nom complet",
        }),
    )
    telephone = forms.CharField(
        max_length=10,
        min_length=10,
        required=True,
        label="Téléphone",
        widget=forms.TextInput(attrs={
            "class": "w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500",
            "placeholder": "Ex: 9712345678",
            "pattern": "[0-9]{10}",
            "maxlength": "10",
        }),
        help_text="10 chiffres sans espaces (l'indicatif +229 sera ajouté automatiquement)",
    )

    def clean_telephone(self):
        telephone = self.cleaned_data.get("telephone", "")
        telephone = telephone.strip()
        
        if not re.match(r"^\d{10}$", telephone):
            raise ValidationError("Le numéro doit contenir exactement 10 chiffres.")
        
        return f"+229{telephone}"

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ["username", "email", "password1", "password2"]:
            self.fields[field_name].widget.attrs.update({
                "class": "w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500",
            })
        self.fields["username"].widget.attrs["placeholder"] = "Nom d'utilisateur"
        self.fields["email"].widget.attrs["placeholder"] = "Adresse email"
        self.fields["email"].required = True
        self.fields["password1"].widget.attrs["placeholder"] = "Mot de passe"
        self.fields["password2"].widget.attrs["placeholder"] = "Confirmer le mot de passe"

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            Proprietaire.objects.create(
                user=user,
                nom_complet=self.cleaned_data["nom_complet"],
                telephone=self.cleaned_data.get("telephone", ""),
            )
        return user
