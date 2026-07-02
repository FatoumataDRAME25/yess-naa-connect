from django.urls import path
from.import views


urlpatterns = [
    path('', views.inscription_producteur, name= 'inscription'),
    path('connexion/', views.connexion_producteur, name= 'connexion'),
    path('dashbord/', views.dashbord, name= 'dashbord'),
    path('commandes/', views.commandes, name= 'commandes'),
    path('profil/', views.profil, name= 'profil'),
    path('declaration/', views.declaration, name= 'declaration'),
]
