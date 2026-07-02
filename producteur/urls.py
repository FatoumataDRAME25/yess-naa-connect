from django.urls import path
from.import views
from.views import InscriptionView,ConnexionView

urlpatterns = [
    path('', InscriptionView.as_view(), name= 'inscription'),
    path('connexion/', ConnexionView.as_view(), name= 'connexion'),
    path('dashbord/', views.dashbord, name= 'dashbord'),
    path('commandes/', views.commandes, name= 'commandes'),
    path('profil/', views.profil, name= 'profil'),
    path('declaration/', views.declaration, name= 'declaration'),
]
