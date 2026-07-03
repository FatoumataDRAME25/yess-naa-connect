from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'admin_transformatrice'

urlpatterns = [
    # Racine → redirige vers connexion
    path('', RedirectView.as_view(pattern_name='admin_transformatrice:admin_login'), name='index'),

    # Authentification
    path('connexion/', views.admin_login, name='admin_login'),
    path('deconnexion/', views.admin_logout, name='admin_logout'),

    # Tableau de bord
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Stocks producteurs
    path('stocks/', views.admin_stocks, name='admin_stocks'),
    path('stocks/commander/', views.admin_commander_paddy, name='admin_commander_paddy'),
    path('stocks/commandes-paddy/', views.admin_commandes_paddy, name='admin_commandes_paddy'),
    path('stocks/commandes-paddy/<int:pk>/recu/', views.admin_marquer_paddy_recu, name='admin_marquer_paddy_recu'),
    path('stocks/commandes-paddy/<int:pk>/statut/', views.admin_commande_paddy_statut, name='admin_commande_paddy_statut'),

    # Catalogue
    path('catalogue/', views.admin_catalogue, name='admin_catalogue'),
    path('catalogue/ajouter/', views.admin_produit_create, name='admin_produit_create'),
    path('catalogue/<int:pk>/modifier/', views.admin_produit_edit, name='admin_produit_edit'),
    path('catalogue/<int:pk>/supprimer/', views.admin_produit_delete, name='admin_produit_delete'),

    # Commandes clients
    path('commandes/', views.admin_commandes, name='admin_commandes'),
    path('commandes/<int:pk>/', views.admin_commande_detail, name='admin_commande_detail'),

    # Démo & À propos
    path('a-propos/', views.admin_about, name='admin_about'),

    # QR code téléchargement (admin connecté)
    path('catalogue/<str:lot_code>/qr/', views.admin_qr_download, name='admin_qr_download'),

    # Traçabilité QR (public)
    path('tracabilite/<str:lot_code>/', views.tracabilite_produit, name='tracabilite_produit'),
]
