from django.shortcuts import redirect

def home(request):
    # Redirige la racine "/" vers la page d'accueil du client
    return redirect('accueil')