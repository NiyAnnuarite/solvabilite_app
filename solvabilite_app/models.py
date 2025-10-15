from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class Compagnie(models.Model):
    TYPE_COMPAGNIE_CHOICES = [
        ('ASSURANCE_VIE', 'Assurance Vie'),
        ('ASSURANCE_NON_VIE', 'Assurance Non-Vie'),
        ('ASSURANCE_MIXTE', 'Assurance Mixte'),
        ('REASSUREUR', 'Réassureur'),
        ('INSTITUTION_FINANCIERE', 'Institution Financière'),
    ]

    STATUT_REGLEMENTAIRE_CHOICES = [
        ('AUTORISEE', 'Autorisée'),
        ('SURVEILLANCE', 'Sous surveillance renforcée'),
        ('SUSPENDUE', 'Activité suspendue'),
        ('RETRAIT', 'Retrait d\'agrément'),
    ]

    nom = models.CharField(max_length=200)
    siren = models.CharField(max_length=9, unique=True)
    date_creation = models.DateField()
    capital_social = models.DecimalField(max_digits=15, decimal_places=2)

    # Nouveaux champs
    type_compagnie = models.CharField(max_length=50, choices=TYPE_COMPAGNIE_CHOICES, default='ASSURANCE_VIE')
    statut_reglementaire = models.CharField(max_length=50, choices=STATUT_REGLEMENTAIRE_CHOICES, default='AUTORISEE')
    agrement_acpr = models.CharField(max_length=50, blank=True, verbose_name="Numéro d'agrément ACPR")
    pays = models.CharField(max_length=100, default='France')
    groupe = models.CharField(max_length=200, blank=True, verbose_name="Groupe d'appartenance")
    date_agrement = models.DateField(null=True, blank=True, verbose_name="Date d'agrément")

    # Contact
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)

    # Métadonnées
    date_ajout = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Compagnie d'assurance"
        verbose_name_plural = "Compagnies d'assurance"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.get_type_compagnie_display()})"


class Utilisateur(AbstractUser):
    ROLE_CHOICES = [
        ('ACTUAIRE', 'Actuaire'),
        ('RISK_MANAGER', 'Risk Manager'),
        ('CONTROLEUR', 'Contrôleur de Gestion'),
        ('DG', 'Directeur Général'),
        ('CONSULTANT', 'Consultant'),
        ('ADMIN', 'Administrateur'),
        ('REGULATEUR', 'Régulateur'),
        ('CLIENT', 'Client'),
        ('RH', 'Responsable RH'),  # AJOUTÉ
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CLIENT')  # CORRIGÉ : ajout default
    telephone = models.CharField(max_length=20, blank=True)
    compagnie = models.ForeignKey(Compagnie, on_delete=models.SET_NULL, null=True, blank=True)  # CORRIGÉ : SET_NULL

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

    def get_role_display(self):
        """Retourne l'affichage du rôle"""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)


class DonneesSolvabilite(models.Model):
    compagnie = models.ForeignKey(Compagnie, on_delete=models.CASCADE)
    date_reference = models.DateField(default=timezone.now)

    # Données bilan
    fonds_propres = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    passif_technique = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    prime_annuelle = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Données de bilan détaillées - AJOUTÉES
    placements = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    immobilisations = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    charges_sinistres = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Modules de risque - Capital Requis
    scr_marche = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    scr_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    scr_vie = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    scr_non_vie = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    scr_operational = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Détails des risques - AJOUTÉS pour calcul automatique
    risque_taux = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    risque_actions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    risque_immobilier = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    risque_contrepartie = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    risque_spread = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    concentration = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    mortalite = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    longevite = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    rachat = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    risque_primes = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    risque_sinistres = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    catastrophes = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Données complémentaires
    mcr = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ratio_solvabilite = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Stockage des détails en JSON - AJOUTÉ
    details_risques = models.JSONField(default=dict, blank=True)

    date_saisie = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_reference']
        verbose_name = "Données de Solvabilité"
        verbose_name_plural = "Données de Solvabilité"

    def __str__(self):
        return f"Données {self.compagnie} - {self.date_reference}"

    def save(self, *args, **kwargs):
        """Surcharge pour calcul automatique des totaux"""
        # Calcul automatique des totaux si les détails sont remplis
        if self.risque_taux or self.risque_actions or self.risque_immobilier:
            self.scr_marche = (self.risque_taux + self.risque_actions + self.risque_immobilier)

        if self.risque_contrepartie or self.risque_spread or self.concentration:
            self.scr_credit = (self.risque_contrepartie + self.risque_spread + self.concentration)

        if self.mortalite or self.longevite or self.rachat:
            self.scr_vie = (self.mortalite + self.longevite + self.rachat)

        if self.risque_primes or self.risque_sinistres or self.catastrophes:
            self.scr_non_vie = (self.risque_primes + self.risque_sinistres + self.catastrophes)

        # Sauvegarde des détails en JSON
        self.details_risques = {
            'marche': {
                'taux': float(self.risque_taux),
                'actions': float(self.risque_actions),
                'immobilier': float(self.risque_immobilier),
                'total': float(self.scr_marche)
            },
            'credit': {
                'contrepartie': float(self.risque_contrepartie),
                'spread': float(self.risque_spread),
                'concentration': float(self.concentration),
                'total': float(self.scr_credit)
            },
            'vie': {
                'mortalite': float(self.mortalite),
                'longevite': float(self.longevite),
                'rachat': float(self.rachat),
                'total': float(self.scr_vie)
            },
            'non_vie': {
                'primes': float(self.risque_primes),
                'sinistres': float(self.risque_sinistres),
                'catastrophes': float(self.catastrophes),
                'total': float(self.scr_non_vie)
            }
        }

        super().save(*args, **kwargs)

    @property
    def total_scr(self):
        """Calcule le SCR total automatiquement"""
        try:
            return float(self.scr_marche) + float(self.scr_credit) + float(self.scr_vie) + float(
                self.scr_non_vie) + float(self.scr_operational)
        except (TypeError, ValueError):
            return 0.0
    @property
    def total_actif(self):
        """Calcule le total actif"""
        return self.placements + self.immobilisations

    @property
    def total_passif(self):
        """Calcule le total passif"""
        return self.fonds_propres + self.passif_technique

    @property
    def equilibre_bilan(self):
        """Vérifie l'équilibre du bilan"""
        return self.total_actif - self.total_passif


class CalculSCR(models.Model):
    donnees = models.ForeignKey(DonneesSolvabilite, on_delete=models.CASCADE)
    methode_calcul = models.CharField(max_length=100)
    parametres_calcul = models.JSONField(default=dict)
    resultat_scr = models.DecimalField(max_digits=15, decimal_places=2)
    date_calcul = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Calcul SCR"
        verbose_name_plural = "Calculs SCR"
        ordering = ['-date_calcul']

    def __str__(self):
        return f"SCR {self.resultat_scr} - {self.date_calcul.strftime('%d/%m/%Y')}"

    @property
    def ratio_solvabilite(self):
        """Calcule le ratio de solvabilité"""
        if self.resultat_scr and self.resultat_scr > 0:
            return (float(self.donnees.fonds_propres) / float(self.resultat_scr)) * 100
        return 0