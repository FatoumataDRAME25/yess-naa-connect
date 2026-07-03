from django.views import View
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.core.paginator import Paginator
from datetime import date
from administration.models import User, CommandePaddy
from producteur.models import Producteur, StockPaddy
from .forms import InscriptionProducteurForm, ConnexionForm, ProfilForm, DeclarationPaddyForm

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
        # Rediriger seulement si c'est bien un producteur connecté
        if request.user.is_authenticated and request.user.role == 'producteur':
            return redirect('dashbord')
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
                    return redirect('dashbord')
                else:
                    messages.error(request, "Vous n'avez pas accès à cet espace.")
            else:
                messages.error(request, "Numéro de téléphone ou mot de passe incorrect.")

        return render(request, self.template_name, {'form': form})


@login_required(login_url='/producteur/connexion/')
def dashbord(request):
    # Vérifier que l'utilisateur connecté est bien un producteur
    if request.user.role != 'producteur':
        messages.error(request, "Accès réservé aux producteurs.")
        return redirect('connexion')

    try:
        producteur = Producteur.objects.get(user=request.user)
    except Producteur.DoesNotExist:
        messages.error(request, "Profil producteur introuvable. Contactez l'administrateur.")
        return redirect('connexion')

    stocks = StockPaddy.objects.filter(producteur=producteur).order_by('-date_recolte')

    # Stat cards
    stock_disponible_kg = stocks.filter(
        statut=StockPaddy.Statut.DISPONIBLE
    ).aggregate(total=Sum('quantite_kg'))['total'] or 0

    nb_commandes = CommandePaddy.objects.filter(
        stock__producteur=producteur
    ).count()

    nb_en_attente = CommandePaddy.objects.filter(
        stock__producteur=producteur,
        statut=CommandePaddy.Statut.EN_ATTENTE
    ).count()

    derniere_commande = CommandePaddy.objects.filter(
        stock__producteur=producteur,
        statut__in=[CommandePaddy.Statut.CONFIRMEE, CommandePaddy.Statut.RECUE]
    ).order_by('-cree_le').first()

    context = {
        'user': request.user,
        'today': date.today(),
        'stock_disponible_kg': stock_disponible_kg,
        'nb_commandes': nb_commandes,
        'nb_en_attente': nb_en_attente,
        'derniere_commande': derniere_commande,
        'derniers_stocks': stocks[:5],
    }
    return render(request, 'dashboard_producteur.html', context)


@login_required(login_url='/producteur/connexion/')
def commandes(request):
    producteur = get_object_or_404(Producteur, user=request.user)

    commandes_qs = CommandePaddy.objects.filter(
        stock__producteur=producteur
    ).select_related('stock').order_by('-cree_le')

    # Filtre par statut via GET ?statut=
    filtre = request.GET.get('statut', '')
    if filtre and filtre in CommandePaddy.Statut.values:
        commandes_qs = commandes_qs.filter(statut=filtre)

    # Stats identiques au dashboard (réutilisées dans le header)
    stocks = StockPaddy.objects.filter(producteur=producteur)
    stock_disponible_kg = stocks.filter(
        statut=StockPaddy.Statut.DISPONIBLE
    ).aggregate(total=Sum('quantite_kg'))['total'] or 0

    nb_commandes_total = CommandePaddy.objects.filter(
        stock__producteur=producteur
    ).count()

    nb_en_attente = CommandePaddy.objects.filter(
        stock__producteur=producteur,
        statut=CommandePaddy.Statut.EN_ATTENTE
    ).count()

    derniere_commande = CommandePaddy.objects.filter(
        stock__producteur=producteur,
        statut__in=[CommandePaddy.Statut.CONFIRMEE, CommandePaddy.Statut.RECUE]
    ).order_by('-cree_le').first()

    # Calcul du montant pour chaque commande
    commandes_avec_montant = []
    for cmd in commandes_qs:
        montant = cmd.quantite_commande * cmd.stock.prix_par_kg
        commandes_avec_montant.append({
            'commande': cmd,
            'montant': montant,
        })

    context = {
        'user': request.user,
        'today': date.today(),
        'stock_disponible_kg': stock_disponible_kg,
        'nb_commandes': nb_commandes_total,
        'nb_en_attente': nb_en_attente,
        'derniere_commande': derniere_commande,
        'commandes': commandes_avec_montant,
        'filtre_actif': filtre,
        'nb_resultats': commandes_qs.count(),
        'statuts': CommandePaddy.Statut.choices,
    }
    return render(request, 'comandes.html', context)


@login_required(login_url='/producteur/connexion/')
def accepter_commande(request, pk):
    """Le producteur accepte une commande de paddy → statut CONFIRMEE."""
    producteur = get_object_or_404(Producteur, user=request.user)
    commande = get_object_or_404(
        CommandePaddy,
        pk=pk,
        stock__producteur=producteur,
        statut=CommandePaddy.Statut.EN_ATTENTE
    )
    if request.method == 'POST':
        commande.statut = CommandePaddy.Statut.CONFIRMEE
        commande.save(update_fields=['statut'])
        messages.success(request, f"Commande #{pk} acceptée. L'administrateur peut maintenant créer le produit.")
    return redirect('commandes')


@login_required(login_url='/producteur/connexion/')
def refuser_commande(request, pk):
    """Le producteur refuse une commande → statut ANNULEE, stock redevient DISPONIBLE."""
    producteur = get_object_or_404(Producteur, user=request.user)
    commande = get_object_or_404(
        CommandePaddy,
        pk=pk,
        stock__producteur=producteur,
        statut=CommandePaddy.Statut.EN_ATTENTE
    )
    if request.method == 'POST':
        commande.statut = CommandePaddy.Statut.ANNULEE
        commande.save(update_fields=['statut'])
        # Remettre le stock en disponible
        commande.stock.statut = StockPaddy.Statut.DISPONIBLE
        commande.stock.save(update_fields=['statut'])
        messages.success(request, f"Commande #{pk} refusée. Le stock est de nouveau disponible.")
    return redirect('commandes')


@login_required(login_url='/producteur/connexion/')
def profil(request):
    edit_mode = False
    if request.method == 'POST':
        form = ProfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Vos informations ont été mises à jour.")
            return redirect('profil')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
            edit_mode = True
    else:
        form = ProfilForm(instance=request.user)

    producteur = get_object_or_404(Producteur, user=request.user)
    nb_stocks = StockPaddy.objects.filter(producteur=producteur).count()
    nb_commandes = CommandePaddy.objects.filter(stock__producteur=producteur).count()

    context = {
        'user': request.user,
        'form': form,
        'nb_stocks': nb_stocks,
        'nb_commandes': nb_commandes,
        'edit_mode': edit_mode,
    }
    return render(request, 'profil.html', context)


@login_required(login_url='/producteur/connexion/')
def declaration(request):
    producteur = get_object_or_404(Producteur, user=request.user)

    if request.method == 'POST':
        form = DeclarationPaddyForm(request.POST, request.FILES)  # ← request.FILES pour la photo
        if form.is_valid():
            stock = form.save(commit=False)
            stock.producteur = producteur
            stock.region = form.cleaned_data['region']
            stock.save()
            messages.success(request, "Votre stock a été déclaré avec succès !")
            return redirect('dashbord')
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        initial = {}
        if request.user.adresse:
            initial['region'] = request.user.adresse
        form = DeclarationPaddyForm(initial=initial)

    context = {
        'user': request.user,
        'form': form,
    }
    return render(request, 'declaration_paddy.html', context)


@login_required(login_url='/producteur/connexion/')
def mes_recoltes(request):
    """Liste toutes les déclarations de récolte du producteur avec pagination."""
    if request.user.role != 'producteur':
        messages.error(request, "Accès réservé aux producteurs.")
        return redirect('connexion')

    try:
        producteur = Producteur.objects.get(user=request.user)
    except Producteur.DoesNotExist:
        messages.error(request, "Profil producteur introuvable.")
        return redirect('connexion')

    # Filtrer par statut si demandé
    filtre_statut = request.GET.get('statut', '')
    stocks_qs = StockPaddy.objects.filter(producteur=producteur).order_by('-date_recolte')
    
    if filtre_statut and filtre_statut in StockPaddy.Statut.values:
        stocks_qs = stocks_qs.filter(statut=filtre_statut)

    # Pagination : 10 items par page
    paginator = Paginator(stocks_qs, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Stats pour le header
    stock_disponible_kg = StockPaddy.objects.filter(
        producteur=producteur,
        statut=StockPaddy.Statut.DISPONIBLE
    ).aggregate(total=Sum('quantite_kg'))['total'] or 0

    nb_commandes = CommandePaddy.objects.filter(
        stock__producteur=producteur
    ).count()

    nb_en_attente = CommandePaddy.objects.filter(
        stock__producteur=producteur,
        statut=CommandePaddy.Statut.EN_ATTENTE
    ).count()

    # Counts par statut pour les tabs
    counts = {
        'tous': stocks_qs.model.objects.filter(producteur=producteur).count(),
        'disponible': stocks_qs.model.objects.filter(producteur=producteur, statut=StockPaddy.Statut.DISPONIBLE).count(),
        'commande': stocks_qs.model.objects.filter(producteur=producteur, statut=StockPaddy.Statut.COMMANDE).count(),
        'epuise': stocks_qs.model.objects.filter(producteur=producteur, statut=StockPaddy.Statut.EPUISE).count(),
    }

    context = {
        'user': request.user,
        'today': date.today(),
        'stock_disponible_kg': stock_disponible_kg,
        'nb_commandes': nb_commandes,
        'nb_en_attente': nb_en_attente,
        'page_obj': page_obj,
        'filtre_statut': filtre_statut,
        'counts': counts,
        'nb_resultats': stocks_qs.count(),
    }
    return render(request, 'mes_recoltes.html', context)