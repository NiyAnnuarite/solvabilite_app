from django.urls import path
from . import views

app_name = 'solvabilite_app'

urlpatterns = [
    # Pages publiques
    path('', views.index, name='index'),
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),

    # Tableau de bord principal
    path('tableau-de-bord/', views.tableau_de_bord, name='tableau_de_bord'),

    # Calculs SCR avec permissions
    path('calcul-scr/', views.calcul_scr, name='calcul_scr'),  # Actuaires, Risk Managers, Admin
    path('calcul-scr-avance/', views.calcul_scr_avance, name='calcul_scr_avance'),  # Actuaires, Admin seulement

    # Indicateurs avec filtrage par rôle
    path('indicateurs/', views.indicateurs_solvabilite, name='indicateurs'),

    # Rapports avec permissions
    path('export-pdf/<str:rapport_type>/', views.export_rapport_pdf, name='export_rapport_pdf'),

    # Pages complémentaires
    path('saisie-donnees/', views.saisie_donnees, name='saisie_donnees'),
    path('tableau-bord-executive/', views.tableau_bord_executive, name='tableau_bord_executive'),
    path('tableau-bord-graphiques/', views.tableau_bord_graphiques, name='tableau_bord_graphiques'),
    path('envoyer-declaration/', views.envoyer_declaration_regulateur, name='envoyer_declaration_regulateur'),
    path('api/indicateurs/', views.api_indicateurs, name='api_indicateurs'),
]