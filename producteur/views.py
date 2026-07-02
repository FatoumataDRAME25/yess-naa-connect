from django.shortcuts import render

# Create your views here.


from django.views import View
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from administration.models import User
from producteur.models import Producteur
from .forms import InscriptionProducteurForm, ConnexionForm

class InscriptionView(View):
    template_name = 'inscription.html'
    form_class = InscriptionProducteurForm

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = User.objects.create_producteur(
                        username=form.cleaned_data['telephone'],
                        password=form.cleaned_data['mot_de_passe'],
                        prenom=form.cleaned_data['prenom'],
                        nom=form.cleaned_data['nom'],
                        telephone=form.cleaned_data['telephone'],
                        adresse=form.cleaned_data['region'],
                    )
                    Producteur.objects.create(user=user)

                messages.success(request, "Compte créé avec succès ! Connectez-vous.")
                return redirect('connexion')

            except Exception as e:
                messages.error(request, f"Une erreur est survenue : {e}")

        return render(request, self.template_name, {'form': form})
    


class ConnexionView(View):
    template_name = 'connexion.html'
    form_class = ConnexionForm

    def get(self, request):
        # Si déjà connecté, rediriger vers dashboard
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            telephone = form.cleaned_data['telephone']
            mot_de_passe = form.cleaned_data['mot_de_passe']
            se_souvenir = form.cleaned_data['se_souvenir']

            # Django utilise username pour authenticate
            # notre username = telephone
            user = authenticate(request, username=telephone, password=mot_de_passe)

            if user is not None:
                # Vérifier que c'est bien un producteur
                if user.role == 'producteur':
                    login(request, user)

                    # Gérer "se souvenir de moi"
                    if not se_souvenir:
                        # Session expire à la fermeture du navigateur
                        request.session.set_expiry(0)
                    else:
                        # Session dure 30 jours
                        request.session.set_expiry(60 * 60 * 24 * 30)

                    messages.success(request, f"Bienvenue, {user.prenom} !")
                    return redirect('dashboard')
                else:
                    messages.error(request, "Vous n'avez pas accès à cet espace.")
            else:
                messages.error(request, "Numéro de téléphone ou mot de passe incorrect.")

        return render(request, self.template_name, {'form': form})



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