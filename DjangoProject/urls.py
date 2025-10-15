"""
URL configuration for DjangoProject project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Page d'administration Django
    path('admin/', admin.site.urls),

    # Redirection de la racine vers l'application solvabilité
    path('', RedirectView.as_view(pattern_name='solvabilite_app:index', permanent=False)),

    # Inclusion des URLs de l'application solvabilité
    path('solvabilite/', include('solvabilite_app.urls')),
]

# Configuration pour servir les fichiers médias en mode développement
if settings.DEBUG:  # CORRECTION : DEBUG au lieu de DUG
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personnalisation de l'interface d'administration
admin.site.site_header = "Administration Solvabilité II"
admin.site.site_title = "Portail d'Administration"
admin.site.index_title = "Gestion de l'Application Solvabilité II"