from django.core.management.base import BaseCommand
from solvabilite_app.models import Compagnie
from datetime import date

class Command(BaseCommand):
    help = 'Peuple la base avec les entreprises réglementées Solvabilité II'

    def handle(self, *args, **options):
        # Liste des entreprises réglementées Solvabilité II
        entreprises_data = [
            {
                'nom': 'AXA France',
                'siren': '542107651',
                'type_compagnie': 'ASSURANCE_MIXTE',
                'capital_social': 1500000000,
                'agrement_acpr': 'ACPR-12345',
                'groupe': 'AXA',
                'pays': 'France',
                'date_creation': date(1816, 1, 1)
            },
            {
                'nom': 'CNP Assurances',
                'siren': '335150078',
                'type_compagnie': 'ASSURANCE_VIE',
                'capital_social': 1200000000,
                'agrement_acpr': 'ACPR-12346',
                'groupe': 'CNP',
                'pays': 'France',
                'date_creation': date(1848, 1, 1)
            },
            {
                'nom': 'Generali France',
                'siren': '305596235',
                'type_compagnie': 'ASSURANCE_MIXTE',
                'capital_social': 900000000,
                'agrement_acpr': 'ACPR-12347',
                'groupe': 'Generali',
                'pays': 'France',
                'date_creation': date(1831, 1, 1)
            },
            {
                'nom': 'Allianz France',
                'siren': '702027642',
                'type_compagnie': 'ASSURANCE_NON_VIE',
                'capital_social': 800000000,
                'agrement_acpr': 'ACPR-12348',
                'groupe': 'Allianz',
                'pays': 'France',
                'date_creation': date(1890, 1, 1)
            },
            {
                'nom': 'Groupama',
                'siren': '306138109',
                'type_compagnie': 'ASSURANCE_MIXTE',
                'capital_social': 1100000000,
                'agrement_acpr': 'ACPR-12349',
                'groupe': 'Groupama',
                'pays': 'France',
                'date_creation': date(1848, 1, 1)
            },
            {
                'nom': 'SCOR SE',
                'siren': '562033967',
                'type_compagnie': 'REASSUREUR',
                'capital_social': 1800000000,
                'agrement_acpr': 'ACPR-12350',
                'groupe': 'SCOR',
                'pays': 'France',
                'date_creation': date(1970, 1, 1)
            },
            {
                'nom': 'BNP Paribas Cardif',
                'siren': '341406504',
                'type_compagnie': 'ASSURANCE_VIE',
                'capital_social': 950000000,
                'agrement_acpr': 'ACPR-12351',
                'groupe': 'BNP Paribas',
                'pays': 'France',
                'date_creation': date(1973, 1, 1)
            },
            {
                'nom': 'Crédit Agricole Assurances',
                'siren': '784608477',
                'type_compagnie': 'ASSURANCE_VIE',
                'capital_social': 1300000000,
                'agrement_acpr': 'ACPR-12352',
                'groupe': 'Crédit Agricole',
                'pays': 'France',
                'date_creation': date(1990, 1, 1)
            },
            {
                'nom': 'MACSF',
                'siren': '775665864',
                'type_compagnie': 'ASSURANCE_VIE',
                'capital_social': 450000000,
                'agrement_acpr': 'ACPR-12353',
                'groupe': 'MACSF',
                'pays': 'France',
                'date_creation': date(1960, 1, 1)
            },
            {
                'nom': 'MMA',
                'siren': '332623579',
                'type_compagnie': 'ASSURANCE_MIXTE',
                'capital_social': 700000000,
                'agrement_acpr': 'ACPR-12354',
                'groupe': 'MMA',
                'pays': 'France',
                'date_creation': date(1828, 1, 1)
            }
        ]

        count_created = 0
        count_updated = 0

        for data in entreprises_data:
            compagnie, created = Compagnie.objects.update_or_create(
                siren=data['siren'],
                defaults={
                    'nom': data['nom'],
                    'date_creation': data['date_creation'],
                    'capital_social': data['capital_social'],
                    'type_compagnie': data['type_compagnie'],
                    'agrement_acpr': data['agrement_acpr'],
                    'groupe': data['groupe'],
                    'pays': data['pays'],
                    'email': f"contact@{data['nom'].lower().replace(' ', '').replace('é', 'e').replace('è', 'e')}.com",
                    'telephone': '+33 1 23 45 67 89',
                    'adresse': 'Paris, France',
                    'statut_reglementaire': 'AUTORISEE',
                    'actif': True
                }
            )
            if created:
                count_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Compagnie créée: {compagnie.nom}')
                )
            else:
                count_updated += 1
                self.stdout.write(
                    self.style.WARNING(f'🔄 Compagnie mise à jour: {compagnie.nom}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ {count_created} entreprises créées, {count_updated} mises à jour - Total: {count_created + count_updated} entreprises réglementées'
            )
        )