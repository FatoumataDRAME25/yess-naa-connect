"""
Gestion du mot de passe pour tous les espaces connectés
(administration / transformatrice, producteurs, livreurs).

Deux façons de récupérer l'accès :
1. Seul, par e-mail : l'utilisateur saisit son numéro de téléphone ou son
   e-mail ; si son compte a une adresse e-mail, il reçoit un lien sécurisé
   (usage unique, valable PASSWORD_RESET_TIMEOUT secondes).
2. Avec l'administration : pour les comptes sans e-mail, l'admin génère un
   mot de passe provisoire (voir admin_reinitialiser_mdp), que l'utilisateur
   doit remplacer dès sa connexion suivante (middleware ChangementMotDePasseObligatoire).

Les clients acheteurs n'ont pas de compte : ils ne sont pas concernés.
"""
import logging
import re
import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import User

logger = logging.getLogger(__name__)

# Anti-abus : nombre maximal de demandes de lien par adresse IP et par fenêtre
LIMITE_DEMANDES = 5
FENETRE_SECONDES = 15 * 60

ESPACES = {
    User.Role.ADMIN:      {'nom': "l'espace Transformateurs(trices)", 'connexion': 'admin_transformatrice:admin_login', 'accueil': 'admin_transformatrice:admin_dashboard'},
    User.Role.PRODUCTEUR: {'nom': "l'espace Producteurs(trices)",     'connexion': 'connexion',                         'accueil': 'dashbord'},
    User.Role.LIVREUR:    {'nom': "l'espace Livreur",                 'connexion': 'livreur:connexion',                 'accueil': 'livreur:dashboard'},
}


def _espace(user):
    role = User.Role.ADMIN if user.is_superuser else user.role
    return ESPACES.get(role, ESPACES[User.Role.ADMIN])


def _contexte_support():
    return {
        'support_telephone': settings.CONTACT_SUPPORT_TELEPHONE,
        'support_email': settings.CONTACT_SUPPORT_EMAIL,
    }


def _ip(request):
    transmise = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (transmise.split(',')[0].strip() if transmise else request.META.get('REMOTE_ADDR', '')) or 'inconnue'


def _comptes_correspondants(identifiant):
    """Comptes actifs (admin, producteur, livreur) correspondant au téléphone ou à l'e-mail saisi."""
    identifiant = identifiant.strip()
    if not identifiant:
        return User.objects.none()
    if '@' in identifiant:
        critere = Q(email__iexact=identifiant)
    else:
        chiffres = re.sub(r'\D', '', identifiant)
        if len(chiffres) < 9:
            return User.objects.none()
        # Les 9 derniers chiffres suffisent (« 77 123 45 67 », « +221771234567 »…)
        critere = Q(telephone__endswith=chiffres[-9:]) | Q(username__endswith=chiffres[-9:])
    return User.objects.filter(critere, is_active=True).filter(
        Q(role__in=[User.Role.ADMIN, User.Role.PRODUCTEUR, User.Role.LIVREUR]) | Q(is_superuser=True)
    ).distinct()


def generer_mot_de_passe_provisoire():
    """Mot de passe provisoire lisible (sans caractères ambigus), ex. « kp7m-4tq9 »."""
    alphabet = 'abcdefghjkmnpqrstuvwxyz23456789'
    bloc = lambda: ''.join(secrets.choice(alphabet) for _ in range(4))
    return f"{bloc()}-{bloc()}"


# ---------------------------------------------------------------------------
# 1. « Mot de passe oublié » : demande du lien par e-mail
# ---------------------------------------------------------------------------

def mot_de_passe_oublie(request):
    contexte = _contexte_support()
    if request.method == 'POST':
        identifiant = request.POST.get('identifiant', '').strip()

        cle = f"mdp-oublie:{_ip(request)}"
        nb = cache.get(cle, 0)
        if nb >= LIMITE_DEMANDES:
            contexte.update(identifiant=identifiant, erreur=(
                "Trop de demandes en peu de temps. Réessayez dans 15 minutes "
                "ou contactez l'administration."))
            return render(request, 'compte/mot_de_passe_oublie.html', contexte, status=429)
        cache.set(cle, nb + 1, FENETRE_SECONDES)

        if not identifiant:
            contexte['erreur'] = "Saisissez votre numéro de téléphone ou votre adresse e-mail."
            return render(request, 'compte/mot_de_passe_oublie.html', contexte)

        for user in _comptes_correspondants(identifiant):
            if not user.email or not user.has_usable_password():
                continue
            lien = request.build_absolute_uri(reverse('compte:reinitialiser', kwargs={
                'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            }))
            corps = render_to_string('compte/email_reinitialisation.txt', {
                'user': user,
                'lien': lien,
                'espace': _espace(user)['nom'],
                'duree_minutes': settings.PASSWORD_RESET_TIMEOUT // 60,
                **_contexte_support(),
            })
            try:
                send_mail(
                    "Réinitialisation de votre mot de passe — YEESNAA CONNECT",
                    corps, settings.DEFAULT_FROM_EMAIL, [user.email],
                )
            except Exception:  # serveur e-mail indisponible : on n'expose rien à l'utilisateur
                logger.exception("Envoi de l'e-mail de réinitialisation impossible (utilisateur %s)", user.pk)

        # Réponse identique que le compte existe ou non (ne révèle pas les numéros inscrits)
        return redirect('compte:mot_de_passe_oublie_envoye')

    return render(request, 'compte/mot_de_passe_oublie.html', contexte)


def mot_de_passe_oublie_envoye(request):
    return render(request, 'compte/mot_de_passe_oublie_envoye.html', _contexte_support())


# ---------------------------------------------------------------------------
# 2. Lien reçu par e-mail : choix du nouveau mot de passe
# ---------------------------------------------------------------------------

class ReinitialisationView(PasswordResetConfirmView):
    template_name = 'compte/reinitialiser.html'
    success_url = reverse_lazy('compte:reinitialisation_terminee')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_contexte_support())
        return ctx

    def form_valid(self, form):
        user = form.user
        user.doit_changer_mdp = False
        user.save(update_fields=['doit_changer_mdp'])
        self.request.session['reinit_connexion_url'] = reverse(_espace(user)['connexion'])
        return super().form_valid(form)


def reinitialisation_terminee(request):
    connexion = request.session.pop('reinit_connexion_url', None) or reverse('accueil')
    return render(request, 'compte/reinitialisation_terminee.html', {'connexion_url': connexion})


# ---------------------------------------------------------------------------
# 3. Mot de passe provisoire : choix obligatoire d'un nouveau mot de passe
# ---------------------------------------------------------------------------

@login_required(login_url='/')
def nouveau_mot_de_passe(request):
    user = request.user
    if not user.doit_changer_mdp:
        return redirect(_espace(user)['accueil'])
    form = SetPasswordForm(user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        user.doit_changer_mdp = False
        user.save(update_fields=['doit_changer_mdp'])
        update_session_auth_hash(request, user)
        messages.success(request, "Votre nouveau mot de passe est enregistré.")
        return redirect(_espace(user)['accueil'])
    return render(request, 'compte/nouveau_mot_de_passe.html', {
        'form': form,
        'espace': _espace(user),
    })


# ---------------------------------------------------------------------------
# 4. Changer son mot de passe une fois connecté (utilisé par l'espace livreur)
# ---------------------------------------------------------------------------

@login_required(login_url='/')
def changer_mot_de_passe(request):
    user = request.user
    form = PasswordChangeForm(user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Votre mot de passe a été modifié.")
        return redirect(_page_profil(user))
    return render(request, 'compte/changer_mot_de_passe.html', {
        'form': form,
        'retour_url': reverse(_page_profil(user)),
    })


def _page_profil(user):
    if user.role == User.Role.LIVREUR and not user.is_superuser:
        return 'livreur:profil'
    return _espace(user)['accueil']
