from django.shortcuts import render

# Create your views here.

def inscription_producteur(request):
    return render(request,'inscription.html')


def connexion_producteur(request):
    return render(request,'connexion.html')

def dashbord(request):
    return render(request, 'dashboard_producteur.html')


def commandes(request):
    return render(request, 'comandes.html')


def profil(request):
    return render(request, 'profil.html')


def declaration(request):
    return render(request, 'declaration_paddy.html')