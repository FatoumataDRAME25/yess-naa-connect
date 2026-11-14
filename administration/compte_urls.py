from django.urls import path

from . import compte

app_name = 'compte'

urlpatterns = [
    path('mot-de-passe-oublie/', compte.mot_de_passe_oublie, name='mot_de_passe_oublie'),
    path('mot-de-passe-oublie/envoye/', compte.mot_de_passe_oublie_envoye, name='mot_de_passe_oublie_envoye'),
    path('reinitialiser/<uidb64>/<token>/', compte.ReinitialisationView.as_view(), name='reinitialiser'),
    path('reinitialiser/termine/', compte.reinitialisation_terminee, name='reinitialisation_terminee'),
    path('nouveau-mot-de-passe/', compte.nouveau_mot_de_passe, name='nouveau_mot_de_passe'),
    path('changer-mot-de-passe/', compte.changer_mot_de_passe, name='changer_mot_de_passe'),
]
