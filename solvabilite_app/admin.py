from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Compagnie, DonneesSolvabilite, CalculSCR


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'compagnie', 'is_staff')
    list_filter = ('role', 'compagnie', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'compagnie__nom')

    fieldsets = UserAdmin.fieldsets + (
        ('Informations Professionnelles', {
            'fields': ('role', 'telephone', 'compagnie')
        }),
    )

    # Pour l'inscription, afficher ces champs
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations Professionnelles', {
            'fields': ('role', 'telephone', 'compagnie')
        }),
    )


@admin.register(Compagnie)
class CompagnieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'siren', 'date_creation', 'capital_social')
    list_filter = ('date_creation',)
    search_fields = ('nom', 'siren')


@admin.register(DonneesSolvabilite)
class DonneesSolvabiliteAdmin(admin.ModelAdmin):
    list_display = ('compagnie', 'date_reference', 'fonds_propres', 'total_scr', 'ratio_solvabilite')
    list_filter = ('date_reference', 'compagnie')
    search_fields = ('compagnie__nom',)
    readonly_fields = ('date_saisie',)

    fieldsets = (
        ('Informations Générales', {
            'fields': ('compagnie', 'date_reference')
        }),
        ('Données Bilan', {
            'fields': ('fonds_propres', 'passif_technique', 'prime_annuelle')
        }),
        ('Modules de Risque SCR', {
            'fields': ('scr_marche', 'scr_credit', 'scr_vie', 'scr_non_vie', 'scr_operational')
        }),
        ('Indicateurs', {
            'fields': ('mcr', 'ratio_solvabilite')
        }),
    )


@admin.register(CalculSCR)
class CalculSCRAdmin(admin.ModelAdmin):
    list_display = ('donnees', 'date_calcul', 'methode_calcul', 'resultat_scr')
    list_filter = ('date_calcul', 'methode_calcul')
    search_fields = ('donnees__compagnie__nom', 'methode_calcul')
    readonly_fields = ('date_calcul',)

    fieldsets = (
        ('Informations Générales', {
            'fields': ('donnees', 'methode_calcul')
        }),
        ('Résultats', {
            'fields': ('resultat_scr', 'parametres_calcul')
        }),
    )