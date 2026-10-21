from datetime import date

from django import forms

from .models import Paiement, TypePaiement


class PaiementEntreeForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ["locataire", "montant_paye", "reste", "date_paiement"]
        widgets = {
            "locataire": forms.Select(attrs={"class": "w-full border rounded px-3 py-2"}),
            "montant_paye": forms.NumberInput(
                attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0"}
            ),
            "reste": forms.NumberInput(
                attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0"}
            ),
            "date_paiement": forms.DateInput(
                attrs={"class": "w-full border rounded px-3 py-2", "type": "date"}
            ),
        }
        labels = {
            "locataire": "Locataire",
            "montant_paye": "Montant payé (FCFA)",
            "reste": "Reste à payer (FCFA)",
            "date_paiement": "Date du paiement",
        }

    def __init__(self, *args, proprietaire=None, **kwargs):
        super().__init__(*args, **kwargs)
        from locahome.locataires.models import Locataire

        self.fields["locataire"].queryset = Locataire.objects.filter(
            chambre__maison__proprietaire=proprietaire,
            statut="EN_COURS",
        ) if proprietaire else Locataire.objects.none()
        if not self.instance.pk:
            self.fields["date_paiement"].initial = date.today()

    def clean_date_paiement(self):
        date_paiement = self.cleaned_data.get("date_paiement")
        if date_paiement and date_paiement > date.today():
            raise forms.ValidationError("La date de paiement ne peut pas être dans le futur.")
        return date_paiement


class PaiementMensuelForm(forms.ModelForm):
    MOIS_CHOICES = [
        (1, "Janvier"), (2, "Février"), (3, "Mars"), (4, "Avril"),
        (5, "Mai"), (6, "Juin"), (7, "Juillet"), (8, "Août"),
        (9, "Septembre"), (10, "Octobre"), (11, "Novembre"), (12, "Décembre"),
    ]
    
    mois = forms.ChoiceField(
        choices=MOIS_CHOICES,
        widget=forms.Select(attrs={"class": "w-full border rounded px-3 py-2"}),
        label="Mois concerné",
    )
    
    class Meta:
        model = Paiement
        fields = ["locataire", "montant_paye", "reste", "mois", "annee", "date_paiement"]
        widgets = {
            "locataire": forms.Select(attrs={"class": "w-full border rounded px-3 py-2"}),
            "montant_paye": forms.NumberInput(
                attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0"}
            ),
            "reste": forms.NumberInput(
                attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0"}
            ),
            "annee": forms.NumberInput(
                attrs={"class": "w-full border rounded px-3 py-2", "min": "2000", "max": "2100"}
            ),
            "date_paiement": forms.DateInput(
                attrs={"class": "w-full border rounded px-3 py-2", "type": "date"}
            ),
        }
        labels = {
            "locataire": "Locataire",
            "montant_paye": "Montant payé (FCFA)",
            "reste": "Reste à payer (FCFA)",
            "annee": "Année concernée",
            "date_paiement": "Date du paiement",
        }

    def __init__(self, *args, proprietaire=None, **kwargs):
        super().__init__(*args, **kwargs)
        from locahome.locataires.models import Locataire

        self.fields["locataire"].queryset = Locataire.objects.filter(
            chambre__maison__proprietaire=proprietaire,
            statut="EN_COURS",
        ) if proprietaire else Locataire.objects.none()
        if not self.instance.pk:
            self.fields["date_paiement"].initial = date.today()
            self.fields["mois"].initial = date.today().month
            self.fields["annee"].initial = date.today().year

    def clean_date_paiement(self):
        date_paiement = self.cleaned_data.get("date_paiement")
        if date_paiement and date_paiement > date.today():
            raise forms.ValidationError("La date de paiement ne peut pas être dans le futur.")
        return date_paiement
    
    def clean(self):
        cleaned_data = super().clean()
        montant_paye = cleaned_data.get("montant_paye")
        reste = cleaned_data.get("reste")
        
        # Vérifier que au moins un montant est renseigné
        if not montant_paye and not reste:
            raise forms.ValidationError("Vous devez renseigner un montant payé ou un reste à payer.")
        
        return cleaned_data


class PaiementSortieForm(forms.Form):
    """
    Formulaire de sortie adapté selon le type de décompteur:
    - CARTE: kwh_sortie + prix_kwh
    - CLASSIQUE: montant_facture_electricite
    - Dans les deux cas: montant_facture_eau
    """
    
    locataire = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={"class": "w-full border rounded px-3 py-2"}),
        label="Locataire",
    )
    
    date_sortie = forms.DateField(
        widget=forms.DateInput(attrs={"class": "w-full border rounded px-3 py-2", "type": "date"}),
        label="Date de sortie",
    )
    
    # Champs pour décompteur à CARTE
    kwh_sortie = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0"}
        ),
        label="Index KWh à la sortie",
        help_text="Index relevé sur le compteur à carte.",
    )
    prix_kwh = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0"}
        ),
        label="Prix du KWh (FCFA)",
        help_text="Prix unitaire du KWh.",
    )
    
    # Champs pour décompteur CLASSIQUE
    montant_facture_electricite = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0"}
        ),
        label="Montant facture électricité (FCFA)",
        help_text="Montant de la facture d'électricité du mois de sortie.",
    )
    
    # Champ commun: facture eau
    montant_facture_eau = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(
            attrs={"class": "w-full border rounded px-3 py-2", "step": "0.01", "min": "0"}
        ),
        label="Montant facture eau (FCFA)",
        help_text="Montant de la facture d'eau du mois de sortie.",
    )
    
    # Champs pour dommages/problèmes
    description_dommages = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "w-full border rounded px-3 py-2",
                "rows": 3,
                "placeholder": "Quel problème avez-vous remarqué ? (ex: trou dans le mur, vitre cassée, serrure abîmée...)",
            }
        ),
        label="Autres problèmes liés à la chambre",
        help_text="Décrivez les dégâts ou problèmes causés par le locataire.",
    )
    montant_dommages = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        widget=forms.NumberInput(
            attrs={"class": "w-full border rounded px-3 py-2", "step": "1", "min": "0"}
        ),
        label="Coût des dommages (FCFA)",
        help_text="Montant estimé des réparations. Sera déduit du solde.",
    )

    def __init__(self, *args, locataire=None, proprietaire=None, **kwargs):
        super().__init__(*args, **kwargs)
        from locahome.locataires.models import Locataire
        
        self.fields["locataire"].queryset = Locataire.objects.filter(
            chambre__maison__proprietaire=proprietaire,
            statut="EN_COURS",
        ) if proprietaire else Locataire.objects.none()
        
        if not self.initial.get("date_sortie"):
            self.initial["date_sortie"] = date.today()
        
        # Pré-remplir si locataire fourni
        if locataire:
            self.initial["locataire"] = locataire.pk
            self.locataire_obj = locataire
        else:
            self.locataire_obj = None

    def clean_date_sortie(self):
        date_sortie = self.cleaned_data.get("date_sortie")
        if date_sortie and date_sortie > date.today():
            raise forms.ValidationError("La date de sortie ne peut pas être dans le futur.")
        return date_sortie

    def clean(self):
        cleaned_data = super().clean()
        locataire = cleaned_data.get("locataire")
        
        if not locataire:
            return cleaned_data
        
        from locahome.chambres.models import TypeDecompteur
        
        type_decompteur = locataire.chambre.type_decompteur
        
        if type_decompteur == TypeDecompteur.CARTE:
            kwh_sortie = cleaned_data.get("kwh_sortie")
            prix_kwh = cleaned_data.get("prix_kwh")
            
            if kwh_sortie is None:
                self.add_error("kwh_sortie", "Ce champ est requis pour un décompteur à carte.")
            if prix_kwh is None:
                self.add_error("prix_kwh", "Ce champ est requis pour un décompteur à carte.")
        else:
            montant_facture = cleaned_data.get("montant_facture_electricite")
            if montant_facture is None:
                self.add_error("montant_facture_electricite", "Ce champ est requis pour un décompteur classique.")
        
        return cleaned_data
