from functools import wraps

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from administration.models import User


class LivreurRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Bloque l'accès à toute vue de l'espace livreur si l'utilisateur connecté
    n'a pas le rôle 'livreur'. Redirige vers la page de connexion livreur
    (pas la connexion admin/producteur) si non connecté.
    """
    login_url = 'livreur:connexion'

    def test_func(self):
        return self.request.user.role == User.Role.LIVREUR


def livreur_required(view_func):
    """Équivalent de LivreurRequiredMixin pour les vues basées fonctions (FBV)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('livreur:connexion')
        if request.user.role != User.Role.LIVREUR:
            return redirect('livreur:connexion')
        return view_func(request, *args, **kwargs)
    return wrapper
