from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from datetime import datetime
import os
from django.conf import settings


def generate_rapport_solvabilite_pdf(donnees, compagnie, rapport_type='DETAIL'):
    """
    Génère un rapport PDF de solvabilité utilisant xhtml2pdf
    """
    try:
        # Préparation du contexte
        context = {
            'donnees': donnees,
            'compagnie': compagnie,
            'date_generation': datetime.now(),
            'rapport_type': rapport_type,
            'statut': get_statut_ratio(donnees.ratio_solvabilite) if hasattr(donnees, 'ratio_solvabilite') else 'N/A'
        }

        # Rendu du template HTML
        html_string = render_to_string('solvabilite_app/rapports/rapport_solvabilite.html', context)

        # Création du PDF
        buffer = BytesIO()
        pdf = pisa.CreatePDF(
            BytesIO(html_string.encode("UTF-8")),
            dest=buffer,
            encoding='UTF-8'
        )

        if pdf.err:
            raise Exception("Erreur lors de la génération du PDF")

        buffer.seek(0)
        return buffer.getvalue()

    except Exception as e:
        # Fallback vers un PDF simple avec reportlab
        return generate_rapport_simple(donnees, compagnie)


def generate_rapport_simple(donnees, compagnie):
    """
    Génère un rapport PDF simple avec reportlab (fallback)
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    # En-tête
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 800, "RAPPORT DE SOLVABILITÉ II")
    p.setFont("Helvetica", 10)
    p.drawString(50, 780, f"Compagnie: {compagnie.nom}")
    p.drawString(50, 765, f"Date: {datetime.now().strftime('%d/%m/%Y')}")

    # Résultats principaux
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 730, "RÉSULTATS PRINCIPAUX")
    p.setFont("Helvetica", 10)

    y_position = 710
    if hasattr(donnees, 'scr_total'):
        p.drawString(50, y_position, f"SCR Total: {donnees.scr_total:,.2f} €")
        y_position -= 15

    if hasattr(donnees, 'fonds_propres_tier1'):
        p.drawString(50, y_position, f"Fonds Propres Tier 1: {donnees.fonds_propres_tier1:,.2f} €")
        y_position -= 15

    if hasattr(donnees, 'ratio_solvabilite'):
        statut = get_statut_ratio(donnees.ratio_solvabilite)
        p.drawString(50, y_position, f"Ratio de Solvabilité: {donnees.ratio_solvabilite}% ({statut})")
        y_position -= 15

    p.save()
    buffer.seek(0)
    return buffer.getvalue()


def get_statut_ratio(ratio):
    """Détermine le statut basé sur le ratio"""
    if ratio >= 180:
        return "EXCELLENT"
    elif ratio >= 150:
        return "BON"
    elif ratio >= 100:
        return "SURVEILLANCE"
    else:
        return "CRITIQUE"