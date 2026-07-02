from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import InscriptionView, ConnexionView

urlpatterns = [
    path('', InscriptionView.as_view(), name='inscription'),
    path('connexion/', ConnexionView.as_view(), name='connexion'),
    path('deconnexion/', auth_views.LogoutView.as_view(next_page='connexion'), name='deconnexion'),
    path('dashbord/', views.dashbord, name='dashbord'),
    path('commandes/', views.commandes, name='commandes'),
    path('profil/', views.profil, name='profil'),
    path('declaration/', views.declaration, name='declaration'),
    path('profil/mot-de-passe/', auth_views.PasswordChangeView.as_view(
        template_name='changer_mot_de_passe.html',
        success_url='/producteur/profil/',
    ), name='changer_mot_de_passe'),
]
