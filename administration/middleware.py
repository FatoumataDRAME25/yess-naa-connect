from django.shortcuts import redirect
from django.urls import reverse


class ChangementMotDePasseObligatoire:
    """
    Après un mot de passe provisoire (réinitialisé par l'admin), l'utilisateur
    est redirigé vers la page « Nouveau mot de passe » tant qu'il n'en a pas
    choisi un. Seules cette page, la déconnexion et les fichiers restent accessibles.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated and getattr(user, 'doit_changer_mdp', False):
            autorisees = {
                reverse('compte:nouveau_mot_de_passe'),
                reverse('admin_transformatrice:admin_logout'),
                reverse('deconnexion'),
                reverse('livreur:deconnexion'),
            }
            chemin = request.path
            if chemin not in autorisees and not chemin.startswith(('/static/', '/media/')):
                return redirect('compte:nouveau_mot_de_passe')
        return self.get_response(request)
