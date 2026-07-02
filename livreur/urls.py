from django.urls import path

from . import views

app_name = 'livreur'

urlpatterns = [
    path('connexion/', views.connexion_livreur, name='connexion'),
    path('deconnexion/', views.deconnexion_livreur, name='deconnexion'),
    path('', views.dashboard, name='dashboard'),
    path('livraison/<int:pk>/', views.detail_livraison, name='detail_livraison'),
    path('livraison/<int:pk>/confirmer/', views.confirmer_livraison, name='confirmer_livraison'),
    path('livraison/<int:pk>/confirmation/', views.confirmation_livraison, name='confirmation'),
    path('profil/', views.profil, name='profil'),
]
