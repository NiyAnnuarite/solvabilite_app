import requests
from django.conf import settings
from datetime import datetime
import json


class RegulateurAPIClient:
    """
    Client pour l'API du régulateur (ACPR, EIOPA, etc.)
    """

    def __init__(self):
        self.base_url = getattr(settings, 'REGULATEUR_API_URL', 'https://api.regulateur.demo')
        self.api_key = getattr(settings, 'REGULATEUR_API_KEY', 'demo-key')

    def envoyer_declaration_solvabilite(self, donnees_solvabilite):
        """
        Envoie la déclaration de solvabilité au régulateur
        """
        try:
            # Préparation des données pour l'API régulateur
            payload = {
                'compagnie_siren': donnees_solvabilite.compagnie.siren if hasattr(donnees_solvabilite.compagnie,
                                                                                  'siren') else '000000000',
                'date_reference': datetime.now().strftime('%Y-%m-%d'),
                'scr_total': float(donnees_solvabilite.scr_total) if hasattr(donnees_solvabilite, 'scr_total') else 0,
                'fonds_propres_tier1': float(donnees_solvabilite.fonds_propres_tier1) if hasattr(donnees_solvabilite,
                                                                                                 'fonds_propres_tier1') else 0,
                'ratio_solvabilite': float(donnees_solvabilite.ratio_solvabilite) if hasattr(donnees_solvabilite,
                                                                                             'ratio_solvabilite') else 0,
                'mcr': float(donnees_solvabilite.mcr) if hasattr(donnees_solvabilite, 'mcr') else 0
            }

            # En mode développement, simuler l'envoi
            if settings.DEBUG:
                return {
                    'success': True,
                    'reference': f"REF_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'message': 'Déclaration simulée avec succès (mode développement)'
                }

            # Envoi réel à l'API (à adapter avec les vraies endpoints)
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f'{self.base_url}/api/declarations/solvabilite',
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'reference': response.json().get('reference'),
                    'message': 'Déclaration envoyée avec succès'
                }
            else:
                return {
                    'success': False,
                    'error': f"Erreur API: {response.status_code} - {response.text}"
                }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"Erreur de connexion: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Erreur inattendue: {str(e)}"
            }


class MarketDataClient:
    """
    Client pour les données de marché (taux, volatilités, etc.)
    """

    def __init__(self):
        self.base_url = getattr(settings, 'MARKET_DATA_URL', 'https://api.marketdata.demo')
        self.api_key = getattr(settings, 'MARKET_DATA_KEY', 'demo-key')

    def get_risk_free_rate(self):
        """
        Récupère le taux sans risque (OAT 10 ans pour l'EUR)
        """
        try:
            # En mode développement, retourner une valeur simulée
            if settings.DEBUG:
                return 0.025  # 2.5%

            headers = {'Authorization': f'Bearer {self.api_key}'}
            response = requests.get(
                f'{self.base_url}/api/rates/risk-free',
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                return response.json().get('rate', 0.025)
            else:
                return 0.025  # Fallback

        except:
            return 0.025  # Fallback en cas d'erreur

    def get_volatility_index(self, asset_class):
        """
        Récupère l'indice de volatilité pour une classe d'actifs
        """
        volatilities = {
            'equity': 1.15,  # +15% de volatilité pour les actions
            'credit': 1.08,  # +8% pour le crédit
            'rates': 1.05,  # +5% pour les taux
            'fx': 1.10,  # +10% pour le forex
            'real_estate': 1.12  # +12% pour l'immobilier
        }

        return volatilities.get(asset_class, 1.0)

    def get_stress_scenario_parameters(self, scenario_type):
        """
        Retourne les paramètres pour différents scénarios de stress
        """
        scenarios = {
            'marche_baissier': {
                'equity_shock': -0.20,
                'credit_spread_shock': 0.015,
                'real_estate_shock': -0.15
            },
            'crise_credit': {
                'equity_shock': -0.10,
                'credit_spread_shock': 0.025,
                'real_estate_shock': -0.10
            },
            'catastrophe_naturelle': {
                'non_life_shock': 0.30,
                'equity_shock': -0.05
            }
        }

        return scenarios.get(scenario_type, {})