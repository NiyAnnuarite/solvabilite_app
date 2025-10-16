# Outil de Mesure de la Solvabilité (Solvabilité II)

## Description
Application web pour le calcul des indicateurs de solvabilité selon le cadre réglementaire Solvabilité II : SCR, MCR et fonds propres éligibles.

## Fonctionnalités
- Calcul du Capital de Solvabilité Requis (SCR)
- Calcul du Minimum Capital Requirement (MCR) 
- Gestion des fonds propres éligibles
- Visualisation des résultats et rapports
- Interface utilisateur intuitive

## Installation

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de packages Python)

### Étapes d'installation

1. **Cloner le repository**
git clone https://github.com/NiyAnnuarite/solvabilite_app.git
cd solvabilite_app

2. ***Créer un environnement virtuel:***

   python -m venv venv
   source venv/bin/activate   # sur Linux/Mac
   venv\Scripts\activate    # sur Windows
   
3. ***Installer les dépendances:**
   pip install -r requirements.txt
   
4. *** Lancer l'application:`***
   python manage.py runserver
   Puis ouvrir  http://127.0.0.1:8000/ dans le navigateur.
