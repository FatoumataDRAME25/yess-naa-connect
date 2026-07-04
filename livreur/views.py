from urllib.parse import quote

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from administration.models import User
from .forms import LivreurLoginForm
from .mixins import livreur_required
from .models import Livraison


def connexion_livreur(request):
    """
    Connexion par téléphone + mot de passe.
    On ne stocke pas le username Django tel quel : on retrouve l'utilisateur
    via son numéro de téléphone, puis on authentifie avec son 'username' réel.
    """
    if request.user.is_authenticated and request.user.role == User.Role.LIVREUR:
        return redirect('livreur:dashboard')

    form = LivreurLoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        telephone = form.cleaned_data['telephone']
        password = form.cleaned_data['password']

        try:
            candidat = User.objects.get(telephone=telephone, role=User.Role.LIVREUR)
        except User.DoesNotExist:
            form.add_error(None, "Numéro de téléphone ou mot de passe incorrect.")
        else:
            user = authenticate(request, username=candidat.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('livreur:dashboard')
            form.add_error(None, "Numéro de téléphone ou mot de passe incorrect.")

    return render(request, 'livreur/connexion.html', {'form': form})


@login_required(login_url='livreur:connexion')
def deconnexion_livreur(request):
    logout(request)
    return redirect('livreur:connexion')


@livreur_required
def dashboard(request):
    """
    Liste UNIQUEMENT les livraisons assignées au livreur connecté, pour aujourd'hui.
    C'est ce filtre qui garantit que chaque livreur voit son propre espace.
    """
    aujourdhui = timezone.localdate()
    livraisons = (
        Livraison.objects
        .filter(livreur=request.user, commande__date__date=aujourdhui)
        .select_related('commande', 'commande__client')
        .prefetch_related('commande__lignes__produit')
        .order_by('confirme_le', '-commande__date')
    )

    a_livrer = [l for l in livraisons if not l.confirme_le]
    total_a_encaisser = sum(
        (l.commande.total for l in a_livrer if l.commande.mode_paiement == 'livraison'),
        0,
    )

    contexte = {
        'livraisons': livraisons,
        'total_livraisons': livraisons.count(),
        'total_a_encaisser': total_a_encaisser,
        'aujourdhui': aujourdhui,
    }

    template = 'livreur/dashboard.html' if livraisons else 'livreur/dashboard_empty.html'
    return render(request, template, contexte)


@livreur_required
def detail_livraison(request, pk):
    livraison = get_object_or_404(
        Livraison.objects.select_related('commande', 'commande__client').prefetch_related('commande__lignes__produit'),
        pk=pk,
        livreur=request.user,  # empêche un livreur de voir la livraison d'un autre
    )
    tracking_url = request.build_absolute_uri(
        reverse('suivre_commande') + f'?numero={livraison.commande.numero}'
    )
    qr_url = f'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={quote(tracking_url)}'
    return render(request, 'livreur/detail_livraison.html', {'livraison': livraison, 'qr_url': qr_url})


@livreur_required
def confirmer_livraison(request, pk):
    livraison = get_object_or_404(Livraison, pk=pk, livreur=request.user)

    if request.method == 'POST' and not livraison.confirme_le:
        montant = livraison.commande.total if livraison.commande.mode_paiement == 'especes' else 0
        livraison.confirmer(montant=montant)

    return redirect('livreur:confirmation', pk=livraison.pk)


@livreur_required
def confirmation_livraison(request, pk):
    livraison = get_object_or_404(Livraison, pk=pk, livreur=request.user)
    return render(request, 'livreur/confirmation.html', {'livraison': livraison})


@livreur_required
def profil(request):
    return render(request, 'livreur/profil.html', {'livreur': request.user})