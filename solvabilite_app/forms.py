from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Utilisateur, Compagnie, DonneesSolvabilite
from datetime import date


class InscriptionForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Adresse email")
    first_name = forms.CharField(required=True, label="Prénom")
    last_name = forms.CharField(required=True, label="Nom")
    role = forms.ChoiceField(choices=Utilisateur.ROLE_CHOICES, label="Rôle")

    # CORRECTION : Utiliser "compagnie" au lieu de "compagnie_nom"
    COMPAGNIE_CHOICES = [
        ('', 'Sélectionnez votre entreprise'),
        ('AXA', 'AXA'),
        ('ALLIANZ', 'Allianz'),
        ('GROUPAMA', 'Groupama'),
        ('GENERALI', 'Generali'),
        ('CNP_ASSURANCES', 'CNP Assurances'),
        ('MACIF', 'MACIF'),
        ('MAIF', 'MAIF'),
        ('MMA', 'MMA'),
        ('ACER', 'Acer'),
        ('AUTRE', 'Autre compagnie'),
    ]

    compagnie = forms.ChoiceField(
        choices=COMPAGNIE_CHOICES,
        required=True,
        label="Entreprise/Compagnie"
    )

    class Meta:
        model = Utilisateur
        fields = ['email', 'first_name', 'last_name', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supprimer le champ username car nous utilisons l'email
        if 'username' in self.fields:
            del self.fields['username']

    def clean_email(self):
        """Valider que l'email est unique"""
        email = self.cleaned_data.get('email')
        if Utilisateur.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = self.cleaned_data['role']

        # Utiliser l'email comme username
        user.username = self.cleaned_data['email']

        # CORRECTION COMPLÈTE : Gestion robuste des compagnies avec SIREN uniques
        compagnie_nom = self.cleaned_data['compagnie']

        if compagnie_nom and compagnie_nom != 'AUTRE':
            # Mapping des SIREN uniques pour chaque compagnie
            siren_mapping = {
                'AXA': '552120222',
                'ALLIANZ': '552120223',
                'GROUPAMA': '552120224',
                'GENERALI': '552120225',
                'CNP_ASSURANCES': '552120226',
                'MACIF': '552120227',
                'MAIF': '552120228',
                'MMA': '552120229',
                'ACER': '552120230',
            }

            siren = siren_mapping.get(compagnie_nom, '000000000')

            # Vérifier d'abord par SIREN, puis par nom
            try:
                # Essayer de trouver par SIREN d'abord (le plus sûr)
                compagnie = Compagnie.objects.get(siren=siren)
            except Compagnie.DoesNotExist:
                try:
                    # Sinon essayer par nom
                    compagnie = Compagnie.objects.get(nom=compagnie_nom)
                except Compagnie.DoesNotExist:
                    # Créer une nouvelle compagnie avec des valeurs par défaut réalistes
                    compagnie = Compagnie.objects.create(
                        nom=compagnie_nom,
                        siren=siren,
                        date_creation=date(2000, 1, 1),
                        capital_social=100000000,  # 100 millions €
                        type_compagnie='ASSURANCE_VIE',
                        statut_reglementaire='AUTORISEE',
                        pays='France',
                        email=f"contact@{compagnie_nom.lower().replace(' ', '')}.com",
                        telephone='+33 1 23 45 67 89',
                        adresse=f"Siège social {compagnie_nom}, Paris, France"
                    )

            user.compagnie = compagnie

        if commit:
            user.save()
        return user


class DonneesSolvabiliteForm(forms.ModelForm):
    class Meta:
        model = DonneesSolvabilite
        fields = [
            'date_reference',
            'fonds_propres',
            'passif_technique',
            'prime_annuelle',
            'placements',
            'immobilisations',
            'charges_sinistres',
            'scr_marche',
            'scr_credit',
            'scr_vie',
            'scr_non_vie',
            'scr_operational',
            'risque_taux',
            'risque_actions',
            'risque_immobilier',
            'risque_contrepartie',
            'risque_spread',
            'concentration',
            'mortalite',
            'longevite',
            'rachat',
            'risque_primes',
            'risque_sinistres',
            'catastrophes',
            'mcr',
            'ratio_solvabilite'
        ]
        widgets = {
            'date_reference': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fonds_propres': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'passif_technique': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prime_annuelle': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'placements': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'immobilisations': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'charges_sinistres': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter des classes Bootstrap à tous les champs
        for field_name, field in self.fields.items():
            if isinstance(field, forms.DecimalField):
                field.widget.attrs.update({'class': 'form-control', 'step': '0.01'})
            elif isinstance(field, forms.DateField):
                field.widget.attrs.update({'class': 'form-control'})


class CompagnieForm(forms.ModelForm):
    class Meta:
        model = Compagnie
        fields = [
            'nom', 'siren', 'date_creation', 'capital_social',
            'type_compagnie', 'statut_reglementaire', 'agrement_acpr',
            'pays', 'groupe', 'date_agrement', 'email', 'telephone', 'adresse'
        ]
        widgets = {
            'date_creation': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_agrement': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'siren': forms.TextInput(attrs={'class': 'form-control'}),
            'capital_social': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'type_compagnie': forms.Select(attrs={'class': 'form-control'}),
            'statut_reglementaire': forms.Select(attrs={'class': 'form-control'}),
            'agrement_acpr': forms.TextInput(attrs={'class': 'form-control'}),
            'pays': forms.TextInput(attrs={'class': 'form-control'}),
            'groupe': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_siren(self):
        """Valider que le SIREN est unique"""
        siren = self.cleaned_data.get('siren')
        if Compagnie.objects.filter(siren=siren).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ce SIREN existe déjà.")
        return siren


class CalculSCRForm(forms.Form):
    """Formulaire pour le calcul simplifié du SCR"""
    fonds_propres = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label="Fonds Propres Éligibles (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True})
    )
    passif_technique = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label="Passif Technique (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True})
    )
    prime_annuelle = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label="Prime Annuelle (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True})
    )
    capital_requis_marche = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label="Capital Requis - Risque Marché (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True})
    )
    capital_requis_credit = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label="Capital Requis - Risque Crédit (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True})
    )
    capital_requis_vie = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label="Capital Requis - Risque Vie (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True})
    )
    capital_requis_non_vie = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label="Capital Requis - Risque Non-Vie (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True})
    )
    date_reference = forms.DateField(
        label="Date de référence",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()

        # Vérifier que tous les champs obligatoires sont remplis
        required_fields = [
            'fonds_propres', 'passif_technique', 'prime_annuelle',
            'capital_requis_marche', 'capital_requis_credit',
            'capital_requis_vie', 'capital_requis_non_vie'
        ]

        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, "Ce champ est obligatoire")

        return cleaned_data


class CalculSCRAvanceForm(forms.Form):
    """Formulaire pour le calcul avancé du SCR avec sous-risques"""

    # Données de base
    fonds_propres = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Fonds Propres Éligibles (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True})
    )
    passif_technique = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Passif Technique (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'required': True})
    )
    prime_annuelle = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Prime Annuelle (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    placements = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Placements (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    immobilisations = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Immobilisations (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    charges_sinistres = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Charges Sinistres (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )

    # Risque Marché - Détail
    risque_taux = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Risque de Taux (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0'})
    )
    risque_actions = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Risque Actions (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0'})
    )
    risque_immobilier = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Risque Immobilier (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0'})
    )

    # Risque Crédit - Détail
    risque_contrepartie = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Risque Contrepartie (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0'})
    )
    risque_spread = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Risque Spread (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0'})
    )
    concentration = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Concentration (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0'})
    )

    # Risque Vie - Détail
    mortalite = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Mortalité (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0'})
    )
    longevite = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Longévité (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0'})
    )
    rachat = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Rachat (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0'})
    )

    # Risque Non-Vie - Détail
    risque_primes = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Risque Primes (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0'})
    )
    risque_sinistres = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Risque Sinistres (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0'})
    )
    catastrophes = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Catastrophes (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0'})
    )

    # Risque Opérationnel
    scr_operational = forms.DecimalField(
        max_digits=15, decimal_places=2,
        label="Risque Opérationnel (M€)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0'})
    )

    date_reference = forms.DateField(
        label="Date de référence",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def clean(self):
        """Validation globale du formulaire avancé"""
        cleaned_data = super().clean()

        # Vérifier les champs obligatoires
        if not cleaned_data.get('fonds_propres'):
            self.add_error('fonds_propres', "Les fonds propres sont obligatoires")

        if not cleaned_data.get('passif_technique'):
            self.add_error('passif_technique', "Le passif technique est obligatoire")

        return cleaned_data


class ProfilUtilisateurForm(forms.ModelForm):
    """Formulaire de mise à jour du profil utilisateur"""

    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'email', 'role', 'compagnie', 'telephone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'compagnie': forms.Select(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        """Valider que l'email est unique (sauf pour l'utilisateur actuel)"""
        email = self.cleaned_data.get('email')
        if Utilisateur.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email


class ConnexionForm(forms.Form):
    """Formulaire de connexion personnalisé"""
    email = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'votre@email.com'})
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Votre mot de passe'})
    )

    def clean(self):
        """Validation de la connexion"""
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            # Vérifier si l'utilisateur existe avec cet email
            try:
                user = Utilisateur.objects.get(email=email)
                # Utiliser l'authentification Django standard
                from django.contrib.auth import authenticate
                user_auth = authenticate(username=user.username, password=password)
                if user_auth is None:
                    raise forms.ValidationError("Email ou mot de passe incorrect.")
            except Utilisateur.DoesNotExist:
                raise forms.ValidationError("Email ou mot de passe incorrect.")

        return cleaned_data