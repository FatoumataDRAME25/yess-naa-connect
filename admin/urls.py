from django.urls import path
from . import views

app_name = 'admin_transformatrice'

urlpatterns = [
    # Authentification
    path('connexion/', views.admin_login, name='admin_login'),
    path('deconnexion/', views.admin_logout, name='admin_logout'),

    # Tableau de bord
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Stocks producteurs
    path('stocks/', views.admin_stocks, name='admin_stocks'),
    path('stocks/commander/', views.admin_commander_paddy, name='admin_commander_paddy'),

    # Catalogue
    path('catalogue/', views.admin_catalogue, name='admin_catalogue'),
    path('catalogue/ajouter/', views.admin_produit_create, name='admin_produit_create'),
    path('catalogue/<int:pk>/modifier/', views.admin_produit_edit, name='admin_produit_edit'),
    path('catalogue/<int:pk>/supprimer/', views.admin_produit_delete, name='admin_produit_delete'),

    # Commandes clients
    path('commandes/', views.admin_commandes, name='admin_commandes'),
    path('commandes/<int:pk>/', views.admin_commande_detail, name='admin_commande_detail'),
]
