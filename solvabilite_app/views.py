from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q, Sum, Avg, Max
from django.http import HttpResponseForbidden, JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from .models import DonneesSolvabilite, CalculSCR, Compagnie, Utilisateur
from .forms import InscriptionForm, DonneesSolvabiliteForm, CalculSCRForm, CalculSCRAvanceForm
from decimal import Decimal
import json
from datetime import datetime, timedelta
import csv
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
from functools import wraps


# =============================================
# DÉCORATEURS DE PERMISSIONS
# =============================================

def role_requis(roles_autorises):
    """Décorateur pour restreindre l'accès aux rôles spécifiés"""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in roles_autorises:
                messages.error(request, "Accès non autorisé pour votre rôle.")
                return redirect('solvabilite_app:tableau_de_bord')
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def permission_requise(permission_requise):
    """Décorateur basé sur les permissions métier"""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_role = request.user.role
            permissions = get_user_permissions(user_role)

            if permission_requise not in permissions:
                messages.error(request, "Vous n'avez pas les permissions nécessaires pour cette action.")
                return redirect('solvabilite_app:tableau_de_bord')
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def get_user_permissions(role):
    """Retourne les permissions selon le rôle"""
    permissions_map = {
        'ACTUAIRE': ['calcul_scr', 'calcul_avance', 'voir_indicateurs', 'exporter_rapports',
                     'voir_rapports_techniques'],
        'RISK_MANAGER': ['calcul_scr', 'voir_indicateurs', 'exporter_rapports', 'voir_rapports_risques',
                         'gestion_risques'],
        'CONTROLEUR': ['voir_indicateurs', 'exporter_rapports', 'voir_rapports_conformite'],
        'DG': ['voir_indicateurs', 'exporter_rapports', 'voir_rapports_strategiques', 'prise_decision'],
        'CLIENT': ['voir_indicateurs_publics', 'voir_rapports_publics'],
        'CONSULTANT': ['voir_indicateurs', 'exporter_rapports', 'analyses_consultation'],
        'REGULATEUR': ['voir_indicateurs', 'exporter_rapports', 'supervision', 'audit'],
        'ADMIN': ['toutes_permissions'],
        'RH': ['gestion_utilisateurs', 'voir_indicateurs_rh']
    }
    return permissions_map.get(role, [])


# =============================================
# VUES PRINCIPALES AVEC PERMISSIONS
# =============================================

def index(request):
    """Vue principale de l'application"""
    if request.user.is_authenticated:
        return redirect('solvabilite_app:tableau_de_bord')
    return render(request, 'solvabilite_app/index.html')


def inscription(request):
    """Vue d'inscription"""
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Inscription réussie ! Bienvenue dans l'application de solvabilité.")
            return redirect('solvabilite_app:tableau_de_bord')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = InscriptionForm()

    return render(request, 'solvabilite_app/inscription.html', {'form': form})


def connexion(request):
    """Vue de connexion"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bienvenue {user.first_name} !")
                next_url = request.GET.get('next', 'solvabilite_app:tableau_de_bord')
                return redirect(next_url)
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = AuthenticationForm()

    return render(request, 'solvabilite_app/connexion.html', {'form': form})


def deconnexion(request):
    """Vue de déconnexion"""
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('solvabilite_app:index')


@login_required
def tableau_de_bord(request):
    """Tableau de bord principal personnalisé par rôle"""
    compagnie = getattr(request.user, 'compagnie', None)
    donnees_recentes = None
    indicateurs = {}
    user_role = request.user.role

    if compagnie:
        donnees_recentes = DonneesSolvabilite.objects.filter(
            compagnie=compagnie
        ).order_by('-date_reference').first()

        # Calcul des indicateurs
        if donnees_recentes:
            statut, couleur_statut = determiner_statut_solvabilite(donnees_recentes.ratio_solvabilite)
            indicateurs = {
                'ratio_solvabilite': donnees_recentes.ratio_solvabilite,
                'scr_total': donnees_recentes.total_scr,
                'mcr': donnees_recentes.mcr,
                'statut': statut,
                'couleur_statut': couleur_statut,
                'fonds_propres': donnees_recentes.fonds_propres,
            }

    # Données spécifiques par rôle
    donnees_specifiques = get_donnees_tableau_bord(user_role, compagnie, request.user)

    context = {
        'compagnie': compagnie,
        'donnees_recentes': donnees_recentes,
        'indicateurs': indicateurs,
        'user_role': user_role,
        'donnees_specifiques': donnees_specifiques,
        'permissions': get_user_permissions(user_role)
    }

    return render(request, 'solvabilite_app/tableau_de_bord.html', context)


def get_donnees_tableau_bord(role, compagnie, user):
    """Retourne les données spécifiques au rôle pour le tableau de bord"""
    donnees = {}

    if role == 'ACTUAIRE':
        # Données pour les actuaires
        donnees['calculs_recents'] = CalculSCR.objects.filter(
            donnees__compagnie=compagnie
        ).order_by('-date_calcul')[:5]
        donnees['alertes_calculs'] = [
            "Vérification des modèles requis",
            "Calcul du SCR trimestriel à planifier"
        ]

    elif role == 'RISK_MANAGER':
        # Données pour les risk managers
        donnees['risques_principaux'] = [
            {"nom": "Risque Marché", "niveau": "Élevé", "tendance": "Stable"},
            {"nom": "Risque Crédit", "niveau": "Moyen", "tendance": "En baisse"},
        ]
        donnees['alertes_risques'] = [
            "Surveillance renforcée du risque marché",
            "Revue des contreparties en cours"
        ]

    elif role == 'CONTROLEUR':
        # Données pour les contrôleurs
        donnees['indicateurs_conformite'] = [
            {"nom": "Ratio SCR", "valeur": "145%", "statut": "Conforme"},
            {"nom": "MCR", "valeur": "Respecté", "statut": "Conforme"},
        ]

    elif role == 'DG':
        # Données pour les directeurs généraux
        donnees['vues_strategiques'] = [
            {"titre": "Position Solvabilité", "valeur": "Excellente", "icone": "fa-chart-line"},
            {"titre": "Risques Majeurs", "valeur": "Contrôlés", "icone": "fa-shield-alt"},
        ]

    elif role == 'CLIENT':
        # Données pour les clients
        donnees['mes_infos'] = [
            {"titre": "Mon Ratio", "valeur": "165%", "statut": "Conforme"},
            {"titre": "Prochain Rapport", "valeur": "15/01/2024", "statut": "En préparation"},
        ]

    elif role == 'CONSULTANT':
        # Données pour les consultants
        donnees['analyses_en_cours'] = [
            "Analyse comparative des ratios",
            "Benchmark des pratiques sectorielles"
        ]

    elif role == 'REGULATEUR':
        # Données pour les régulateurs
        donnees['supervision_data'] = [
            {"compagnie": "AssurPlus", "ratio": "198%", "statut": "Conforme"},
            {"compagnie": "SecureAssur", "ratio": "145%", "statut": "Surveillance"},
        ]

    elif role == 'ADMIN':
        # Données pour les administrateurs
        donnees['stats_systeme'] = {
            'utilisateurs_actifs': Utilisateur.objects.filter(is_active=True).count(),
            'calculs_jour': CalculSCR.objects.filter(date_calcul__date=datetime.now().date()).count(),
            'compagnies_actives': Compagnie.objects.filter(utilisateur__is_active=True).distinct().count()
        }

    elif role == 'RH':
        # Données pour les RH
        donnees['stats_rh'] = {
            'total_utilisateurs': Utilisateur.objects.filter(compagnie=compagnie).count(),
            'par_role': Utilisateur.objects.filter(compagnie=compagnie).values('role').annotate(total=Count('id'))
        }

    return donnees


# =============================================
# CALCULS SCR AVEC PERMISSIONS
# =============================================

@login_required
@role_requis(['ACTUAIRE', 'RISK_MANAGER', 'ADMIN'])
def calcul_scr(request):
    """
    Vue pour le calcul standard du SCR - Réservé aux Actuaires, Risk Managers et Admin
    """
    # Vérification supplémentaire dans la vue
    if request.user.role not in ['ACTUAIRE', 'RISK_MANAGER', 'ADMIN']:
        messages.error(request, "Accès réservé aux actuaires et risk managers.")
        return redirect('solvabilite_app:tableau_de_bord')

    resultats = None
    compagnie_utilisateur = None

    if hasattr(request.user, 'compagnie') and request.user.compagnie:
        compagnie_utilisateur = request.user.compagnie

    derniere_saisie = None
    if compagnie_utilisateur:
        derniere_saisie = DonneesSolvabilite.objects.filter(
            compagnie=compagnie_utilisateur
        ).order_by('-date_reference').first()

    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            fonds_propres = Decimal(request.POST.get('fonds_propres', 0))
            passif_technique = Decimal(request.POST.get('passif_technique', 0))
            prime_annuelle = Decimal(request.POST.get('prime_annuelle', 0))

            # Modules de risque
            capital_requis_marche = Decimal(request.POST.get('capital_requis_marche', 0))
            capital_requis_credit = Decimal(request.POST.get('capital_requis_credit', 0))
            capital_requis_vie = Decimal(request.POST.get('capital_requis_vie', 0))
            capital_requis_non_vie = Decimal(request.POST.get('capital_requis_non_vie', 0))

            date_reference = request.POST.get('date_reference', datetime.now().strftime('%Y-%m-%d'))

            # Validation des données obligatoires
            if not all([fonds_propres, passif_technique, prime_annuelle,
                        capital_requis_marche, capital_requis_credit,
                        capital_requis_vie, capital_requis_non_vie]):
                messages.error(request, "Tous les champs obligatoires doivent être remplis")
                return render(request, 'solvabilite_app/calcul_scr.html', {
                    'resultats': None,
                    'compagnie': compagnie_utilisateur,
                    'derniere_saisie': derniere_saisie,
                    'user_role': request.user.role
                })

            # Calcul du SCR selon la formule standard avec corrélations
            scr_total = calculer_scr_standard(
                float(capital_requis_marche),
                float(capital_requis_credit),
                float(capital_requis_vie),
                float(capital_requis_non_vie)
            )

            # Calcul du MCR (Minimum Capital Requirement)
            mcr = calculer_mcr(scr_total, float(prime_annuelle), float(passif_technique))

            # Calcul du ratio de solvabilité
            ratio = (float(fonds_propres) / scr_total * 100) if scr_total > 0 else 0

            # Détermination du statut
            statut, couleur_statut = determiner_statut_solvabilite(ratio)

            # Préparation des résultats pour l'affichage
            resultats = {
                'scr': round(scr_total, 2),
                'mcr': round(mcr, 2),
                'ratio': round(ratio, 2),
                'statut': statut,
                'couleur_statut': couleur_statut,
                'fonds_propres': float(fonds_propres),
                'passif_technique': float(passif_technique),
                'prime_annuelle': float(prime_annuelle),
                'date_reference': date_reference,
                'modules': {
                    'marche': float(capital_requis_marche),
                    'credit': float(capital_requis_credit),
                    'vie': float(capital_requis_vie),
                    'non_vie': float(capital_requis_non_vie),
                }
            }

            # Calcul des pourcentages pour l'affichage
            total_modules = sum(resultats['modules'].values())
            if total_modules > 0:
                for module in resultats['modules']:
                    resultats['modules'][module] = {
                        'valeur': resultats['modules'][module],
                        'pourcentage': round((resultats['modules'][module] / total_modules) * 100, 1)
                    }

            # Sauvegarde des résultats si l'utilisateur est authentifié et a une compagnie
            if request.user.is_authenticated and compagnie_utilisateur:
                sauvegarder_calcul_scr(request.user, compagnie_utilisateur, resultats, 'STANDARD')

            messages.success(request, f"Calcul du SCR terminé : {scr_total:.2f} M€")

        except (ValueError, Exception) as e:
            messages.error(request, f"Erreur dans les données saisies : {str(e)}")

    return render(request, 'solvabilite_app/calcul_scr.html', {
        'resultats': resultats,
        'compagnie': compagnie_utilisateur,
        'derniere_saisie': derniere_saisie,
        'user_role': request.user.role
    })


@login_required
@role_requis(['ACTUAIRE', 'ADMIN'])
def calcul_scr_avance(request):
    """
    Vue pour le calcul avancé du SCR - Réservé aux Actuaires et Admin seulement
    """
    # Vérification supplémentaire
    if request.user.role not in ['ACTUAIRE', 'ADMIN']:
        messages.error(request, "Accès réservé aux actuaires.")
        return redirect('solvabilite_app:tableau_de_bord')

    resultats = None
    compagnie_utilisateur = None

    if hasattr(request.user, 'compagnie') and request.user.compagnie:
        compagnie_utilisateur = request.user.compagnie

    # Charger les dernières données si disponibles
    derniere_saisie = None
    if compagnie_utilisateur:
        derniere_saisie = DonneesSolvabilite.objects.filter(
            compagnie=compagnie_utilisateur
        ).order_by('-date_reference').first()

    if request.method == 'POST':
        try:
            # Données de base
            fonds_propres = Decimal(request.POST.get('fonds_propres', 0))
            passif_technique = Decimal(request.POST.get('passif_technique', 0))
            prime_annuelle = Decimal(request.POST.get('prime_annuelle', 0))
            placements = Decimal(request.POST.get('placements', 0))
            immobilisations = Decimal(request.POST.get('immobilisations', 0))
            charges_sinistres = Decimal(request.POST.get('charges_sinistres', 0))
            date_reference = request.POST.get('date_reference', datetime.now().strftime('%Y-%m-%d'))

            # Sous-risques détaillés - Risque Marché
            risque_taux = Decimal(request.POST.get('risque_taux', 0))
            risque_actions = Decimal(request.POST.get('risque_actions', 0))
            risque_immobilier = Decimal(request.POST.get('risque_immobilier', 0))

            # Sous-risques détaillés - Risque Crédit
            risque_contrepartie = Decimal(request.POST.get('risque_contrepartie', 0))
            risque_spread = Decimal(request.POST.get('risque_spread', 0))
            concentration = Decimal(request.POST.get('concentration', 0))

            # Sous-risques détaillés - Risque Vie
            mortalite = Decimal(request.POST.get('mortalite', 0))
            longevite = Decimal(request.POST.get('longevite', 0))
            rachat = Decimal(request.POST.get('rachat', 0))

            # Sous-risques détaillés - Risque Non-Vie
            risque_primes = Decimal(request.POST.get('risque_primes', 0))
            risque_sinistres = Decimal(request.POST.get('risque_sinistres', 0))
            catastrophes = Decimal(request.POST.get('catastrophes', 0))

            # Risque Opérationnel
            scr_operational = Decimal(request.POST.get('scr_operational', 0))

            # Validation des données minimales
            if not fonds_propres or not passif_technique:
                messages.error(request, "Les données de base (fonds propres et passif technique) sont obligatoires")
                return render(request, 'solvabilite_app/calcul_scr_avance.html', {
                    'resultats': None,
                    'compagnie': compagnie_utilisateur,
                    'derniere_saisie': derniere_saisie,
                    'user_role': request.user.role
                })

            # Calcul des modules de risque à partir des sous-risques
            scr_marche = risque_taux + risque_actions + risque_immobilier
            scr_credit = risque_contrepartie + risque_spread + concentration
            scr_vie = mortalite + longevite + rachat
            scr_non_vie = risque_primes + risque_sinistres + catastrophes

            # Calcul du SCR total avec formule standard
            scr_total = calculer_scr_standard(float(scr_marche), float(scr_credit), float(scr_vie), float(scr_non_vie),
                                              float(scr_operational))

            # Calcul du MCR
            mcr = calculer_mcr(scr_total, float(prime_annuelle), float(passif_technique))

            # Calcul du ratio
            ratio = (float(fonds_propres) / scr_total * 100) if scr_total > 0 else 0
            statut, couleur_statut = determiner_statut_solvabilite(ratio)

            # Préparation des résultats détaillés
            resultats = {
                'scr': round(scr_total, 2),
                'mcr': round(mcr, 2),
                'ratio': round(ratio, 2),
                'statut': statut,
                'couleur_statut': couleur_statut,
                'fonds_propres': float(fonds_propres),
                'passif_technique': float(passif_technique),
                'prime_annuelle': float(prime_annuelle),
                'placements': float(placements),
                'immobilisations': float(immobilisations),
                'charges_sinistres': float(charges_sinistres),
                'date_reference': date_reference,
                'modules': {
                    'marche': float(scr_marche),
                    'credit': float(scr_credit),
                    'vie': float(scr_vie),
                    'non_vie': float(scr_non_vie),
                    'operational': float(scr_operational)
                },
                'sous_risques': {
                    'marche': {
                        'taux': float(risque_taux),
                        'actions': float(risque_actions),
                        'immobilier': float(risque_immobilier)
                    },
                    'credit': {
                        'contrepartie': float(risque_contrepartie),
                        'spread': float(risque_spread),
                        'concentration': float(concentration)
                    },
                    'vie': {
                        'mortalite': float(mortalite),
                        'longevite': float(longevite),
                        'rachat': float(rachat)
                    },
                    'non_vie': {
                        'primes': float(risque_primes),
                        'sinistres': float(risque_sinistres),
                        'catastrophes': float(catastrophes)
                    }
                }
            }

            # Calcul des pourcentages pour l'affichage
            total_modules = sum([resultats['modules']['marche'], resultats['modules']['credit'],
                                 resultats['modules']['vie'], resultats['modules']['non_vie']])
            if total_modules > 0:
                for module in ['marche', 'credit', 'vie', 'non_vie']:
                    resultats['modules'][module] = {
                        'valeur': resultats['modules'][module],
                        'pourcentage': round((resultats['modules'][module] / total_modules) * 100, 1)
                    }

            # Sauvegarde des données détaillées
            if request.user.is_authenticated and compagnie_utilisateur:
                sauvegarder_calcul_avance(request.user, compagnie_utilisateur, resultats)

            messages.success(request, f"Calcul avancé du SCR terminé : {scr_total:.2f} M€")

        except (ValueError, Decimal.InvalidOperation) as e:
            messages.error(request, "Erreur dans les données saisies. Vérifiez les valeurs numériques.")
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors du calcul : {str(e)}")

    return render(request, 'solvabilite_app/calcul_scr_avance.html', {
        'resultats': resultats,
        'compagnie': compagnie_utilisateur,
        'derniere_saisie': derniere_saisie,
        'user_role': request.user.role
    })


# =============================================
# INDICATEURS AVEC FILTRAGE PAR RÔLE
# =============================================

@login_required
def indicateurs_solvabilite(request):
    """Vue pour afficher les indicateurs de solvabilité avec filtrage par rôle"""
    compagnie = getattr(request.user, 'compagnie', None)
    donnees = []
    user_role = request.user.role

    if compagnie:
        # Récupérer toutes les données selon le rôle
        if user_role in ['CLIENT', 'CONSULTANT']:
            # Clients et consultants : données limitées
            toutes_donnees = DonneesSolvabilite.objects.filter(
                compagnie=compagnie,
                date_reference__gte=datetime.now() - timedelta(days=365)  # 12 derniers mois seulement
            ).order_by('date_reference')
        else:
            # Autres rôles : toutes les données
            toutes_donnees = DonneesSolvabilite.objects.filter(
                compagnie=compagnie
            ).order_by('date_reference')

        # Prendre les 12 derniers mois seulement pour l'affichage
        donnees = list(toutes_donnees[:12])

        # Pour la dernière donnée, utiliser le queryset complet
        derniere_donnee = toutes_donnees.last()
    else:
        derniere_donnee = None

    # Préparation des données pour les graphiques
    dates = []
    ratios = []
    scr_totals = []
    fonds_propres_list = []
    modules_data = {
        'marche': [],
        'credit': [],
        'vie': [],
        'non_vie': []
    }

    for donnee in donnees:
        dates.append(donnee.date_reference.strftime('%Y-%m'))
        ratios.append(float(donnee.ratio_solvabilite))
        scr_totals.append(float(donnee.total_scr))
        fonds_propres_list.append(float(donnee.fonds_propres))

        # Modules de risque (limités pour certains rôles)
        if user_role not in ['CLIENT']:  # Les clients ne voient pas le détail des modules
            modules_data['marche'].append(float(donnee.scr_marche))
            modules_data['credit'].append(float(donnee.scr_credit))
            modules_data['vie'].append(float(donnee.scr_vie))
            modules_data['non_vie'].append(float(donnee.scr_non_vie))

    # Dernière donnée pour la répartition (limitée pour clients)
    repartition_modules = {}
    if derniere_donnee and user_role not in ['CLIENT']:
        total_scr = float(derniere_donnee.total_scr)
        if total_scr > 0:
            repartition_modules = {
                'Marche': (float(derniere_donnee.scr_marche) / total_scr) * 100,
                'Credit': (float(derniere_donnee.scr_credit) / total_scr) * 100,
                'Vie': (float(derniere_donnee.scr_vie) / total_scr) * 100,
                'Non-Vie': (float(derniere_donnee.scr_non_vie) / total_scr) * 100,
            }

    context = {
        'compagnie': compagnie,
        'donnees': donnees,
        'user_role': user_role,
        'graphiques_data': {
            'dates': dates,
            'ratios': ratios,
            'scr_totals': scr_totals,
            'fonds_propres': fonds_propres_list,
            'modules': modules_data,
            'repartition': repartition_modules,
        }
    }

    return render(request, 'solvabilite_app/indicateurs.html', context)


# =============================================
# RAPPORTS AVEC PERMISSIONS
# =============================================

@login_required
@permission_requise('exporter_rapports')
def export_rapport_pdf(request, rapport_type):
    """Export de rapport en PDF avec vérification des permissions"""
    user_role = request.user.role

    # Vérification des permissions spécifiques par type de rapport
    if rapport_type == 'technique' and user_role not in ['ACTUAIRE', 'ADMIN']:
        messages.error(request, "Accès aux rapports techniques réservé aux actuaires.")
        return redirect('solvabilite_app:tableau_de_bord')

    elif rapport_type == 'risques' and user_role not in ['RISK_MANAGER', 'ADMIN', 'DG']:
        messages.error(request, "Accès aux rapports risques réservé aux risk managers et direction.")
        return redirect('solvabilite_app:tableau_de_bord')

    try:
        # Créer le buffer PDF
        buffer = io.BytesIO()

        # Créer le document PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1  # Centered
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e')
        )

        normal_style = styles["Normal"]

        # Contenu du PDF
        story = []

        # Titre principal selon le type de rapport
        if rapport_type == 'synthese':
            title_text = "RAPPORT DE SOLVABILITÉ - SYNTHÈSE"
        elif rapport_type == 'detail':
            title_text = "RAPPORT DE SOLVABILITÉ - DÉTAILLÉ"
        elif rapport_type == 'technique':
            title_text = "RAPPORT TECHNIQUE ACTUARIEL"
        elif rapport_type == 'risques':
            title_text = "RAPPORT D'ANALYSE DES RISQUES"
        else:
            title_text = f"RAPPORT DE SOLVABILITÉ - {rapport_type.upper()}"

        title = Paragraph(title_text, title_style)
        story.append(title)
        story.append(Spacer(1, 20))

        # Informations de base
        compagnie = getattr(request.user, 'compagnie', None)
        if compagnie:
            info_text = f"""
            <b>Compagnie:</b> {compagnie.nom}<br/>
            <b>SIREN:</b> {compagnie.siren}<br/>
            <b>Type:</b> {compagnie.get_type_compagnie_display()}<br/>
            <b>Date du rapport:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>
            <b>Généré par:</b> {request.user.get_full_name()} ({request.user.get_role_display()})
            """
        else:
            info_text = f"""
            <b>Utilisateur:</b> {request.user.get_full_name()}<br/>
            <b>Rôle:</b> {request.user.get_role_display()}<br/>
            <b>Date du rapport:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}
            """

        info_paragraph = Paragraph(info_text, normal_style)
        story.append(info_paragraph)
        story.append(Spacer(1, 30))

        # Données récentes
        donnees_recentes = None
        if compagnie:
            donnees_recentes = DonneesSolvabilite.objects.filter(
                compagnie=compagnie
            ).order_by('-date_reference').first()

        if donnees_recentes:
            # Section indicateurs de solvabilité
            story.append(Paragraph("INDICATEURS DE SOLVABILITÉ", heading_style))

            # Calcul des indicateurs
            ratio = float(donnees_recentes.ratio_solvabilite)
            scr_total = float(donnees_recentes.total_scr)
            mcr = float(donnees_recentes.mcr)
            fonds_propres = float(donnees_recentes.fonds_propres)

            # Détermination du statut
            if ratio >= 180:
                statut = "Très Solide"
                couleur_statut = "#27ae60"
            elif ratio >= 150:
                statut = "Solide"
                couleur_statut = "#2ecc71"
            elif ratio >= 120:
                statut = "Conforme"
                couleur_statut = "#3498db"
            elif ratio >= 100:
                statut = "Surveillance"
                couleur_statut = "#f39c12"
            else:
                statut = "Non Conforme"
                couleur_statut = "#e74c3c"

            # Tableau des indicateurs principaux
            indicateurs_data = [
                ['Indicateur', 'Valeur', 'Statut'],
                ['Ratio de Solvabilité', f"{ratio:.1f}%", statut],
                ['SCR Total', f"{scr_total:,.2f} €", 'Capital Requis'],
                ['MCR', f"{mcr:,.2f} €", 'Minimum Réglementaire'],
                ['Fonds Propres', f"{fonds_propres:,.2f} €", 'Capital Disponible'],
                ['Marge de Solvabilité', f"{(fonds_propres - scr_total):,.2f} €", 'Excédent/Déficit']
            ]

            indicateurs_table = Table(indicateurs_data, colWidths=[2.5 * inch, 2 * inch, 2 * inch])
            indicateurs_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7'))
            ]))

            story.append(indicateurs_table)
            story.append(Spacer(1, 20))

            # Répartition des risques
            story.append(Paragraph("RÉPARTITION DU SCR PAR MODULE DE RISQUE", heading_style))

            # Calcul des pourcentages
            total_scr_modules = sum([
                float(donnees_recentes.scr_marche),
                float(donnees_recentes.scr_credit),
                float(donnees_recentes.scr_vie),
                float(donnees_recentes.scr_non_vie)
            ])

            if total_scr_modules > 0:
                modules_data = [
                    ['Module de Risque', 'Montant SCR (€)', 'Pourcentage'],
                    ['Risque Marché', f"{float(donnees_recentes.scr_marche):,.2f}",
                     f"{(float(donnees_recentes.scr_marche) / total_scr_modules * 100):.1f}%"],
                    ['Risque Crédit', f"{float(donnees_recentes.scr_credit):,.2f}",
                     f"{(float(donnees_recentes.scr_credit) / total_scr_modules * 100):.1f}%"],
                    ['Risque Vie', f"{float(donnees_recentes.scr_vie):,.2f}",
                     f"{(float(donnees_recentes.scr_vie) / total_scr_modules * 100):.1f}%"],
                    ['Risque Non-Vie', f"{float(donnees_recentes.scr_non_vie):,.2f}",
                     f"{(float(donnees_recentes.scr_non_vie) / total_scr_modules * 100):.1f}%"]
                ]

                if float(donnees_recentes.scr_operational) > 0:
                    modules_data.append([
                        'Risque Opérationnel',
                        f"{float(donnees_recentes.scr_operational):,.2f}",
                        f"{(float(donnees_recentes.scr_operational) / total_scr_modules * 100):.1f}%"
                    ])
            else:
                modules_data = [
                    ['Module de Risque', 'Montant SCR (€)', 'Pourcentage'],
                    ['Aucune donnée disponible', '-', '-']
                ]

            modules_table = Table(modules_data, colWidths=[2.5 * inch, 2 * inch, 1.5 * inch])
            modules_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6'))
            ]))

            story.append(modules_table)
            story.append(Spacer(1, 25))

            # Analyse et recommandations
            story.append(Paragraph("ANALYSE ET RECOMMANDATIONS", heading_style))

            if ratio >= 180:
                analyse_text = """
                <b>Analyse:</b> La situation de solvabilité est excellente. Le ratio est bien au-dessus des exigences réglementaires.<br/>
                <b>Recommandations:</b> Maintenir la stratégie actuelle. Possibilité d'optimisation du capital.
                """
            elif ratio >= 150:
                analyse_text = """
                <b>Analyse:</b> Situation conforme avec une marge de sécurité confortable.<br/>
                <b>Recommandations:</b> Surveillance continue. Renforcer la gestion des risques principaux.
                """
            elif ratio >= 120:
                analyse_text = """
                <b>Analyse:</b> Situation nécessitant une surveillance renforcée. Le ratio est proche du minimum requis.<br/>
                <b>Recommandations:</b> Plan d'action pour améliorer la solvabilité. Révision de la stratégie de risque.
                """
            else:
                analyse_text = """
                <b>Analyse:</b> Situation critique nécessitant une intervention immédiate.<br/>
                <b>Recommandations:</b> Plan de redressement urgent. Augmentation de capital nécessaire.
                """

            analyse_paragraph = Paragraph(analyse_text, normal_style)
            story.append(analyse_paragraph)

            # Données complémentaires pour rapport détaillé
            if rapport_type == 'detail':
                story.append(Spacer(1, 20))
                story.append(Paragraph("DONNÉES COMPLÉMENTAIRES", heading_style))

                complement_data = [
                    ['Élément', 'Valeur'],
                    ['Prime Annuelle', f"{float(donnees_recentes.prime_annuelle):,.2f} €"],
                    ['Placements', f"{float(donnees_recentes.placements):,.2f} €"],
                    ['Immobilisations', f"{float(donnees_recentes.immobilisations):,.2f} €"],
                    ['Charges Sinistres', f"{float(donnees_recentes.charges_sinistres):,.2f} €"],
                    ['Date de référence', donnees_recentes.date_reference.strftime('%d/%m/%Y')]
                ]

                complement_table = Table(complement_data, colWidths=[3 * inch, 3 * inch])
                complement_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7f8c8d')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7'))
                ]))

                story.append(complement_table)

        else:
            # Aucune donnée disponible
            story.append(Paragraph("AUCUNE DONNÉE DISPONIBLE", heading_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(
                "Aucune donnée de solvabilité n'a été trouvée pour générer le rapport. "
                "Veuillez effectuer des calculs SCR avant de générer un rapport.",
                normal_style
            ))

        # Pied de page
        story.append(Spacer(1, 30))
        footer_text = f"""
        <i>Rapport généré automatiquement par l'Application de Solvabilité II - {datetime.now().strftime('%d/%m/%Y')}</i><br/>
        <i>Ce document est confidentiel et destiné à un usage interne.</i>
        """
        footer_paragraph = Paragraph(footer_text, styles["Italic"])
        story.append(footer_paragraph)

        # Générer le PDF
        doc.build(story)

        # Récupérer le PDF du buffer
        pdf = buffer.getvalue()
        buffer.close()

        # CRÉER LA RÉPONSE HTTP (PARTIE MANQUANTE)
        response = HttpResponse(content_type='application/pdf')
        filename = f"rapport_solvabilite_{rapport_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf)

        return response

    except Exception as e:
        # En cas d'erreur, retourner un message d'erreur
        messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
        return redirect('solvabilite_app:tableau_de_bord')
# =============================================
# FONCTIONS UTILITAIRES (inchangées)
# =============================================

def calculer_scr_standard(scr_marche, scr_credit, scr_vie, scr_non_vie, scr_operational=0):
    """Calcule le SCR total selon la formule standard Solvabilité II"""
    scr_marche = float(scr_marche)
    scr_credit = float(scr_credit)
    scr_vie = float(scr_vie)
    scr_non_vie = float(scr_non_vie)
    scr_operational = float(scr_operational)

    scr_base = 0.0
    scr_base += scr_marche ** 2
    scr_base += scr_credit ** 2
    scr_base += scr_vie ** 2
    scr_base += scr_non_vie ** 2

    correlations = 0.0
    correlations += 0.25 * scr_marche * scr_credit
    correlations += 0.25 * scr_marche * scr_vie
    correlations += 0.5 * scr_marche * scr_non_vie
    correlations += 0.25 * scr_credit * scr_vie
    correlations += 0.25 * scr_credit * scr_non_vie
    correlations += 0.25 * scr_vie * scr_non_vie

    scr_corrige = (scr_base + 2 * correlations) ** 0.5
    scr_total = scr_corrige + scr_operational

    return scr_total


def calculer_mcr(scr, prime_annuelle, passif_technique):
    """Calcule le Minimum Capital Requirement selon Solvabilité II"""
    scr_decimal = Decimal(str(scr))
    prime_annuelle_decimal = Decimal(str(prime_annuelle))
    passif_technique_decimal = Decimal(str(passif_technique))

    mcr_primes = prime_annuelle_decimal * Decimal('0.25')
    mcr_sinistres = passif_technique_decimal * Decimal('0.15')
    mcr_calcule = max(mcr_primes, mcr_sinistres)

    mcr_min = scr_decimal * Decimal('0.25')
    mcr_max = scr_decimal * Decimal('0.45')
    mcr_final = max(mcr_min, min(mcr_calcule, mcr_max))

    return float(mcr_final)


def determiner_statut_solvabilite(ratio):
    """Détermine le statut de solvabilité basé sur le ratio"""
    if ratio >= 180:
        return "Très Solide", "success"
    elif ratio >= 150:
        return "Solide", "info"
    elif ratio >= 120:
        return "Conforme", "primary"
    elif ratio >= 100:
        return "Surveillance", "warning"
    else:
        return "Non Conforme", "danger"


def sauvegarder_calcul_scr(utilisateur, compagnie, resultats, methode):
    """Sauvegarde le calcul du SCR en base de données"""
    try:
        try:
            date_ref = datetime.strptime(resultats['date_reference'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            date_ref = datetime.now().date()

        donnees = DonneesSolvabilite.objects.create(
            compagnie=compagnie,
            date_reference=date_ref,
            fonds_propres=resultats['fonds_propres'],
            passif_technique=resultats['passif_technique'],
            prime_annuelle=resultats['prime_annuelle'],
            scr_marche=resultats['modules']['marche']['valeur'],
            scr_credit=resultats['modules']['credit']['valeur'],
            scr_vie=resultats['modules']['vie']['valeur'],
            scr_non_vie=resultats['modules']['non_vie']['valeur'],
            mcr=resultats['mcr'],
            ratio_solvabilite=resultats['ratio']
        )

        CalculSCR.objects.create(
            donnees=donnees,
            methode_calcul=methode,
            parametres_calcul=resultats,
            resultat_scr=resultats['scr']
        )

    except Exception as e:
        print(f"Erreur sauvegarde calcul SCR: {str(e)}")


def sauvegarder_calcul_avance(utilisateur, compagnie, resultats):
    """Sauvegarde le calcul avancé du SCR avec tous les détails"""
    try:
        try:
            date_ref = datetime.strptime(resultats['date_reference'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            date_ref = datetime.now().date()

        donnees = DonneesSolvabilite.objects.create(
            compagnie=compagnie,
            date_reference=date_ref,
            fonds_propres=resultats['fonds_propres'],
            passif_technique=resultats['passif_technique'],
            prime_annuelle=resultats['prime_annuelle'],
            placements=resultats['placements'],
            immobilisations=resultats['immobilisations'],
            charges_sinistres=resultats['charges_sinistres'],
            scr_marche=resultats['modules']['marche']['valeur'],
            scr_credit=resultats['modules']['credit']['valeur'],
            scr_vie=resultats['modules']['vie']['valeur'],
            scr_non_vie=resultats['modules']['non_vie']['valeur'],
            scr_operational=resultats['modules']['operational'],
            risque_taux=resultats['sous_risques']['marche']['taux'],
            risque_actions=resultats['sous_risques']['marche']['actions'],
            risque_immobilier=resultats['sous_risques']['marche']['immobilier'],
            risque_contrepartie=resultats['sous_risques']['credit']['contrepartie'],
            risque_spread=resultats['sous_risques']['credit']['spread'],
            concentration=resultats['sous_risques']['credit']['concentration'],
            mortalite=resultats['sous_risques']['vie']['mortalite'],
            longevite=resultats['sous_risques']['vie']['longevite'],
            rachat=resultats['sous_risques']['vie']['rachat'],
            risque_primes=resultats['sous_risques']['non_vie']['primes'],
            risque_sinistres=resultats['sous_risques']['non_vie']['sinistres'],
            catastrophes=resultats['sous_risques']['non_vie']['catastrophes'],
            mcr=resultats['mcr'],
            ratio_solvabilite=resultats['ratio'],
            details_risques=resultats['sous_risques']
        )

        CalculSCR.objects.create(
            donnees=donnees,
            methode_calcul="AVANCE",
            parametres_calcul=resultats,
            resultat_scr=resultats['scr']
        )

    except Exception as e:
        print(f"Erreur sauvegarde calcul avancé: {str(e)}")


# =============================================
# VUES COMPLÉMENTAIRES
# =============================================

@login_required
def saisie_donnees(request):
    """Vue pour la saisie manuelle des données"""
    return render(request, 'solvabilite_app/saisie_donnees.html')


@login_required
def tableau_bord_executive(request):
    """Tableau de bord exécutif"""
    return render(request, 'solvabilite_app/tableau_bord_executive.html')


@login_required
def tableau_bord_graphiques(request):
    """Tableau de bord avec graphiques"""
    return render(request, 'solvabilite_app/tableau_bord_graphiques.html')


@login_required
def envoyer_declaration_regulateur(request):
    """Envoi de déclaration au régulateur"""
    return HttpResponse("Déclaration envoyée")


@login_required
def api_indicateurs(request):
    """API pour les indicateurs"""
    return JsonResponse({'status': 'ok'})