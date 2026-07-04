import io
from urllib.parse import quote

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count, F, Q
from django.http import HttpResponse
from django.templatetags.static import static
from django.urls import reverse
from datetime import date, datetime

import qrcode

from producteur.models import StockPaddy
from administration.models import Produit, CommandePaddy, User
from administration.forms import LivreurCreationForm
from client.models import CommandeClient
from livreur.models import Livraison


# ── Décorateur utilitaire : réserve l'accès aux admins ──
def admin_required(view_func):
    @login_required(login_url='/espace-admin/connexion/')
    def wrapper(request, *args, **kwargs):
        if not request.user.role == 'admin' and not request.user.is_superuser:
            messages.error(request, "Accès réservé aux administrateurs.")
            return redirect('admin_transformatrice:admin_login')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ============================================================
#  AUTHENTIFICATION
# ============================================================

def admin_login(request):
    """Connexion de la transformatrice/admin."""
    if request.user.is_authenticated:
        return redirect('admin_transformatrice:admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('admin_transformatrice:admin_dashboard')
        messages.error(request, "Identifiant ou mot de passe incorrect.")
        return render(request, 'espace_admin/login.html', {'has_error': True})
    return render(request, 'espace_admin/login.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_transformatrice:admin_login')


# ============================================================
#  TABLEAU DE BORD
# ============================================================

@admin_required
def admin_dashboard(request):
    today = date.today()

    commandes_jour = CommandeClient.objects.filter(date__date=today).count()
    producteurs_actifs = StockPaddy.objects.filter(
        statut=StockPaddy.Statut.DISPONIBLE
    ).values('producteur').distinct().count()
    stock_paddy_total = StockPaddy.objects.filter(
        statut=StockPaddy.Statut.DISPONIBLE
    ).aggregate(total=Sum('quantite_kg'))['total'] or 0

    ca_mois = CommandeClient.objects.filter(
        date__year=today.year, date__month=today.month
    ).aggregate(
        total=Sum(F('lignes__quantite') * F('lignes__prix_unitaire'))
    )['total'] or 0

    commandes_recentes = CommandeClient.objects.select_related('client').prefetch_related(
        'lignes__produit'
    ).order_by('-date')[:5]

    total_commandes = CommandeClient.objects.count() or 1
    en_livraison = CommandeClient.objects.filter(statut=CommandeClient.Statut.EN_LIVRAISON).count()
    en_attente = CommandeClient.objects.filter(statut=CommandeClient.Statut.ATTENTE).count()

    context = {
        'active_nav': 'dashboard',
        'today': today,
        'stats': {
            'commandes_jour': commandes_jour,
            'ca_mois': f"{int(ca_mois):,}".replace(',', ' '),
            'stock_paddy': f"{int(stock_paddy_total):,}".replace(',', ' '),
            'producteurs_actifs': producteurs_actifs,
        },
        'pct_livraison': round(en_livraison / total_commandes * 100),
        'pct_en_ligne': round(en_attente / total_commandes * 100),
        'commandes_recentes': commandes_recentes,
    }
    return render(request, 'espace_admin/dashboard.html', context)


# ============================================================
#  STOCKS PRODUCTEURS
# ============================================================

@admin_required
def admin_stocks(request):
    commande_envoyee = request.session.pop('commande_envoyee', None)

    q = request.GET.get('q', '').strip()
    region_filtre = request.GET.get('region', '').strip()
    variete_filtre = request.GET.get('variete', '').strip()
    tri = request.GET.get('tri', 'recent')

    # Toujours calculer les stats globales (non filtrées)
    stocks_base = StockPaddy.objects.filter(
        statut__in=[StockPaddy.Statut.DISPONIBLE, StockPaddy.Statut.COMMANDE]
    )
    stock_total_kg = stocks_base.filter(
        statut=StockPaddy.Statut.DISPONIBLE
    ).aggregate(total=Sum('quantite_kg'))['total'] or 0
    nb_producteurs = stocks_base.values('producteur').distinct().count()
    regions = list(stocks_base.values_list('region', flat=True).distinct().order_by('region'))
    varietes = [v[1] for v in StockPaddy.Variete.choices]

    # Stocks filtrés pour l'affichage
    stocks = stocks_base.select_related('producteur__user')

    if q:
        stocks = stocks.filter(
            Q(producteur__user__prenom__icontains=q) |
            Q(producteur__user__nom__icontains=q) |
            Q(region__icontains=q) |
            Q(variete__icontains=q)
        )
    if region_filtre:
        stocks = stocks.filter(region=region_filtre)
    if variete_filtre:
        stocks = stocks.filter(variete=variete_filtre)

    if tri == 'quantite':
        stocks = stocks.order_by('-quantite_kg')
    else:
        stocks = stocks.order_by('-id')

    # Annoter chaque stock avec sa commande active (en_attente ou confirmee)
    commandes_actives = CommandePaddy.objects.filter(
        stock__in=stocks,
        statut__in=[CommandePaddy.Statut.EN_ATTENTE, CommandePaddy.Statut.CONFIRMEE],
    ).select_related('stock')
    commandes_par_stock = {c.stock_id: c for c in commandes_actives}
    for stock in stocks:
        stock.commande_active = commandes_par_stock.get(stock.id)

    context = {
        'active_nav': 'stocks',
        'stock_total_kg': f"{int(stock_total_kg):,}".replace(',', ' '),
        'nb_producteurs': nb_producteurs,
        'regions': regions,
        'varietes': varietes,
        'stocks_producteurs': stocks,
        'commande_envoyee': commande_envoyee,
        'commandes_par_stock': commandes_par_stock,
        'q': q,
        'region_filtre': region_filtre,
        'variete_filtre': variete_filtre,
        'tri': tri,
    }
    return render(request, 'espace_admin/stocks_producteurs.html', context)


@admin_required
def admin_commander_paddy(request):
    if request.method == 'POST':
        stock_id = request.POST.get('stock_id')
        quantite_kg = request.POST.get('quantite_kg', '0')
        date_livraison = request.POST.get('date_livraison', '')
        note = request.POST.get('note', '')

        stock = get_object_or_404(StockPaddy, pk=stock_id)

        try:
            quantite = float(quantite_kg)
        except (ValueError, TypeError):
            messages.error(request, "Quantité invalide.")
            return redirect('admin_transformatrice:admin_stocks')

        if quantite <= 0 or quantite > float(stock.quantite_kg):
            messages.error(request, f"Quantité doit être entre 1 et {stock.quantite_kg} kg.")
            return redirect('admin_transformatrice:admin_stocks')

        date_liv = None
        if date_livraison:
            try:
                date_liv = datetime.strptime(date_livraison, '%Y-%m-%d').date()
            except ValueError:
                pass

        commande = CommandePaddy.objects.create(
            stock=stock,
            commande_par=request.user,
            quantite_commande=quantite,
            date_livraison=date_liv,
            note=note,
            statut=CommandePaddy.Statut.EN_ATTENTE,
        )

        stock.statut = StockPaddy.Statut.COMMANDE
        stock.save(update_fields=['statut'])

        total = quantite * float(stock.prix_par_kg)
        date_fmt = date_liv.strftime('%d/%m/%Y') if date_liv else '—'

        request.session['commande_envoyee'] = {
            'producteur_nom': f"{stock.producteur.user.prenom} {stock.producteur.user.nom}",
            'quantite_kg': quantite_kg,
            'date_livraison': date_fmt,
            'total': f"{int(total):,}".replace(',', ' '),
            'reference': f"#PAD-{commande.pk:04d}",
        }

    return redirect('admin_transformatrice:admin_stocks')


@admin_required
def admin_marquer_paddy_recu(request, pk):
    """L'admin marque une commande paddy comme reçue après livraison physique."""
    commande = get_object_or_404(
        CommandePaddy,
        pk=pk,
        statut=CommandePaddy.Statut.CONFIRMEE
    )
    if request.method == 'POST':
        commande.statut = CommandePaddy.Statut.RECUE
        commande.save(update_fields=['statut'])

        stock = commande.stock
        stock.quantite_kg = max(stock.quantite_kg - commande.quantite_commande, 0)
        stock.statut = (
            StockPaddy.Statut.EPUISE if stock.quantite_kg <= 0 else StockPaddy.Statut.DISPONIBLE
        )
        stock.save(update_fields=['quantite_kg', 'statut'])

        messages.success(
            request,
            f"Commande #{pk} marquée comme reçue. "
            f"Vous pouvez maintenant créer un produit lié à ce lot."
        )
        # Redirige vers le catalogue avec pré-sélection de la commande
        url = reverse('admin_transformatrice:admin_catalogue') + f'?commande_paddy_id={pk}'
        return redirect(url)
    return redirect('admin_transformatrice:admin_stocks')


# ============================================================
#  CATALOGUE
# ============================================================

@admin_required
def admin_catalogue(request):
    produit_publie = request.session.pop('produit_publie', None)
    filtre = request.GET.get('filtre', 'tous')

    # Pré-sélection traçabilité : vient-on d'une commande paddy reçue ?
    commande_paddy_preselect = None
    commande_paddy_id_get = request.GET.get('commande_paddy_id', '').strip()
    if commande_paddy_id_get:
        try:
            commande_paddy_preselect = CommandePaddy.objects.select_related(
                'stock__producteur__user'
            ).get(pk=int(commande_paddy_id_get), statut=CommandePaddy.Statut.RECUE)
        except (CommandePaddy.DoesNotExist, ValueError):
            messages.warning(request, "Commande paddy introuvable ou non reçue.")

    tous_produits = Produit.objects.select_related('stock_source__stock__producteur__user').order_by('-cree_le')

    if filtre == 'en_ligne':
        produits_affiches = tous_produits.filter(est_actif=True, stock_sacs__gt=10)
    elif filtre == 'rupture':
        produits_affiches = tous_produits.filter(est_actif=True, stock_sacs__lte=10)
    else:
        produits_affiches = tous_produits

    total = tous_produits.count()
    en_ligne_count = tous_produits.filter(est_actif=True, stock_sacs__gt=10).count()
    rupture_count = tous_produits.filter(est_actif=True, stock_sacs__lte=10).count()
    produits_stock_faible = tous_produits.filter(est_actif=True, stock_sacs__gt=0, stock_sacs__lte=10)

    # Commandes paddy reçues disponibles pour lier un nouveau produit
    commandes_paddy_recues = CommandePaddy.objects.filter(
        statut=CommandePaddy.Statut.RECUE
    ).select_related('stock__producteur__user').order_by('-cree_le')

    context = {
        'active_nav': 'catalogue',
        'produits': produits_affiches,
        'tous_produits_count': total,
        'en_ligne_count': en_ligne_count,
        'rupture_count': rupture_count,
        'produits_stock_faible': produits_stock_faible,
        'variantes_poids': Produit.Poids.choices,
        'type_riz_choices': Produit.TypeRiz.choices,
        'commandes_paddy': commandes_paddy_recues,
        'commande_paddy_preselect': commande_paddy_preselect,
        'produit_publie': produit_publie,
        'filtre_actif': filtre,
    }
    return render(request, 'espace_admin/catalogue.html', context)


@admin_required
def admin_produit_create(request):
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        type_riz = request.POST.get('type_riz', 'blanc')
        description = request.POST.get('description', '')
        stock_initial = int(request.POST.get('stock_initial') or 0)
        photo = request.FILES.get('photo')
        variantes = request.POST.getlist('variantes')
        commande_paddy_id = request.POST.get('commande_paddy_id', '').strip() 

        if not nom:
            messages.error(request, "Le nom du produit est obligatoire.")
            return redirect('admin_transformatrice:admin_catalogue')

        # Résoudre le lien de traçabilité vers la commande paddy source
        stock_source = None
        if commande_paddy_id:
            try:
                stock_source = CommandePaddy.objects.get(
                    pk=int(commande_paddy_id),
                    statut=CommandePaddy.Statut.RECUE,
                )
            except (CommandePaddy.DoesNotExist, ValueError):
                messages.warning(request, "Commande paddy introuvable ou non reçue — produit créé sans lien de traçabilité.")

        poids_list = [int(p) for p in variantes if p.isdigit()] if variantes else [5]
        produits_crees = []

        for poids in poids_list:
            prix_val = request.POST.get(f'prix_{poids}', '0') or '0'
            try:
                prix = float(prix_val)
            except ValueError:
                prix = 0

            p = Produit.objects.create(
                nom=nom,
                type_riz=type_riz,
                poids_kg=poids,
                prix=prix,
                stock_sacs=stock_initial,
                description=description,
                photo=photo if photo else None,
                est_actif=True,
                stock_source=stock_source,
            )
            produits_crees.append(f"{poids} kg")

        if produits_crees:
            dernier = Produit.objects.filter(nom=nom).order_by('-cree_le').first()
            code = dernier.code_lot
            origine = (
                f"{stock_source.stock.producteur.user.prenom} {stock_source.stock.producteur.user.nom}"
                if stock_source else "Non renseignée"
            )
            tracabilite_url = request.build_absolute_uri(
                reverse('admin_transformatrice:tracabilite_produit', args=[code])
            )
            qr_display_url = (
                f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={quote(tracabilite_url)}"
            )
            request.session['produit_publie'] = {
                'nom': nom,
                'variantes': produits_crees,
                'lot_code': code,
                'origine': origine,
                'qr_url': qr_display_url,
            }
            messages.success(request, f"Produit « {nom} » ajouté avec succès.")

    return redirect('admin_transformatrice:admin_catalogue')


@admin_required
def admin_produit_edit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        if not nom:
            messages.error(request, "Le nom du produit est obligatoire.")
            return redirect('admin_transformatrice:admin_produit_edit', pk=pk)

        produit.nom = nom
        produit.type_riz = request.POST.get('type_riz', produit.type_riz)
        produit.description = request.POST.get('description', produit.description)

        poids_val = request.POST.get('poids_kg', produit.poids_kg)
        try:
            produit.poids_kg = int(poids_val)
            produit.prix = float(request.POST.get('prix', produit.prix))
            produit.stock_sacs = int(request.POST.get('stock_sacs', produit.stock_sacs))
        except (ValueError, TypeError):
            messages.error(request, "Valeurs numériques invalides.")
            return redirect('admin_transformatrice:admin_produit_edit', pk=pk)

        produit.est_actif = request.POST.get('est_actif') == 'on'

        if request.FILES.get('photo'):
            produit.photo = request.FILES['photo']

        produit.save()
        messages.success(request, "Produit mis à jour.")
        return redirect('admin_transformatrice:admin_catalogue')

    context = {
        'active_nav': 'catalogue',
        'produit': produit,
        'poids_choices': Produit.Poids.choices,
        'type_riz_choices': Produit.TypeRiz.choices,
    }
    return render(request, 'espace_admin/catalogue_edit.html', context)


@admin_required
def admin_produit_delete(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        nom = produit.nom
        produit.delete()
        messages.success(request, f"Produit « {nom} » supprimé.")
    return redirect('admin_transformatrice:admin_catalogue')


# ============================================================
#  COMMANDES CLIENTS
# ============================================================

@admin_required
def admin_commandes(request):
    statut_filtre = request.GET.get('statut', 'toutes')
    q = request.GET.get('q', '').strip()

    commandes_qs = CommandeClient.objects.select_related('client').prefetch_related(
        'lignes__produit'
    ).order_by('-date')

    if statut_filtre != 'toutes':
        commandes_qs = commandes_qs.filter(statut=statut_filtre)

    if q:
        commandes_qs = commandes_qs.filter(
            Q(client__prenom__icontains=q) |
            Q(client__nom__icontains=q) |
            Q(client__telephone__icontains=q)
        )

    counts = {s: CommandeClient.objects.filter(statut=s).count() for s, _ in CommandeClient.Statut.choices}
    total_all = CommandeClient.objects.count()

    today = date.today()
    commandes_jour = CommandeClient.objects.filter(date__date=today).count()
    en_attente_count = counts.get('attente', 0)
    en_livraison_count = counts.get('en_livraison', 0)

    paginator = Paginator(commandes_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'active_nav': 'commandes',
        'stats': {
            'total': total_all,
            'en_attente': en_attente_count,
            'en_livraison': en_livraison_count,
            'commandes_jour': commandes_jour,
        },
        'status_tabs': [
            {'label': 'Toutes',         'value': 'toutes',       'count': total_all,                    'active': statut_filtre == 'toutes'},
            {'label': 'En attente',     'value': 'attente',      'count': counts.get('attente', 0),     'active': statut_filtre == 'attente'},
            {'label': 'En préparation', 'value': 'preparation',  'count': counts.get('preparation', 0), 'active': statut_filtre == 'preparation'},
            {'label': 'En livraison',   'value': 'en_livraison', 'count': counts.get('en_livraison', 0),'active': statut_filtre == 'en_livraison'},
            {'label': 'Livrée',         'value': 'livree',       'count': counts.get('livree', 0),      'active': statut_filtre == 'livree'},
            {'label': 'Annulée',        'value': 'annulee',      'count': counts.get('annulee', 0),     'active': statut_filtre == 'annulee'},
        ],
        'commandes': page_obj,
        'paginator': paginator,
        'page_obj': page_obj,
        'statut_filtre': statut_filtre,
        'q': q,
    }
    return render(request, 'espace_admin/commandes.html', context)


@admin_required
def admin_commande_detail(request, pk):
    commande = get_object_or_404(
        CommandeClient.objects.select_related('client').prefetch_related('lignes__produit'),
        pk=pk,
    )

    livraison = Livraison.objects.filter(commande=commande).select_related('livreur').first()

    if request.method == 'POST':

        # ── Cas 1 : assignation / réassignation d'un livreur ──
        if 'livreur_id' in request.POST:
            livreur_id = request.POST.get('livreur_id')
            if not livreur_id:
                messages.error(request, "Veuillez choisir un livreur.")
            else:
                livreur_user = get_object_or_404(User, pk=livreur_id, role=User.Role.LIVREUR)
                if livraison:
                    livraison.livreur = livreur_user
                    livraison.save(update_fields=['livreur'])
                else:
                    livraison = Livraison.objects.create(commande=commande, livreur=livreur_user)

                # Fait passer la commande en livraison si elle était encore en préparation/attente
                if commande.statut in (CommandeClient.Statut.ATTENTE, CommandeClient.Statut.PREPARATION):
                    commande.statut = CommandeClient.Statut.EN_LIVRAISON
                    commande.save(update_fields=['statut'])

                messages.success(
                    request,
                    f"{livreur_user.prenom} {livreur_user.nom} a été assigné(e) à la commande #{commande.numero}."
                )
            return redirect('admin_transformatrice:admin_commande_detail', pk=pk)

        # ── Cas 2 : changement de statut (stepper) ──
        nouveau_statut = request.POST.get('statut')
        statuts_valides = [s for s, _ in CommandeClient.Statut.choices]
        if nouveau_statut in statuts_valides:
            commande.statut = nouveau_statut
            commande.save(update_fields=['statut'])
            messages.success(request, f"Commande #{pk} mise à jour.")
        return redirect('admin_transformatrice:admin_commandes')

    statut = commande.statut
    statut_labels = dict(CommandeClient.Statut.choices)

    livreurs_disponibles = User.objects.filter(role=User.Role.LIVREUR).order_by('prenom', 'nom')

    etapes = [
        {'label': 'Marquer en préparation', 'value': 'preparation',  'active': statut == 'attente'},
        {'label': 'Marquer en livraison',   'value': 'en_livraison', 'active': statut == 'preparation'},
        {'label': 'Marquer livrée',         'value': 'livree',       'active': statut == 'en_livraison'},
    ]

    stepper_steps = [
        ('Attente',     statut in ('preparation', 'en_livraison', 'livree')),
        ('Préparation', statut in ('en_livraison', 'livree')),
        ('Livraison',   statut in ('en_livraison', 'livree')),
        ('Livrée',      statut == 'livree'),
    ]

    # Attributs d'affichage calculés, attachés directement à l'instance pour
    # que le template puisse les lire simplement via `commande.xxx`.
    commande.date_str = commande.date.strftime('%d/%m/%Y')
    commande.heure = commande.date.strftime('%H:%M')
    commande.statut_label = statut_labels.get(statut, statut)

    tracking_url = request.build_absolute_uri(
        reverse('suivre_commande') + f'?numero={commande.numero}'
    )
    commande.qr_url = f'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={quote(tracking_url)}'

    commande.articles = [
        {
            'nom': ligne.produit.nom,
            'photo_url': ligne.produit.photo.url if ligne.produit.photo else static('images/1sac5kg.jpg'),
            'quantite': ligne.quantite,
            'prix_unitaire': ligne.prix_unitaire,
            'sous_total': ligne.ligne_total,
        }
        for ligne in commande.lignes.all()
    ]

    context = {
        'active_nav': 'commandes',
        'commande': commande,
        'etapes': etapes,
        'stepper_steps': stepper_steps,
        'livraison': livraison,
        'livreurs_disponibles': livreurs_disponibles,
    }
    return render(request, 'espace_admin/commande_detail.html', context)


# ============================================================
#  GESTION DES LIVREURS (créés uniquement par l'admin)
# ============================================================

@admin_required
def admin_livreurs(request):
    """
    Liste des comptes livreurs + formulaire de création.
    L'admin choisit le téléphone (= identifiant de connexion) et le mot
    de passe, puis les communique lui-même au livreur.
    """
    form = LivreurCreationForm()

    if request.method == 'POST':
        form = LivreurCreationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_livreur(
                username=form.cleaned_data['telephone'],
                password=form.cleaned_data['mot_de_passe'],
                prenom=form.cleaned_data['prenom'],
                nom=form.cleaned_data['nom'],
                telephone=form.cleaned_data['telephone'],
                adresse=form.cleaned_data.get('adresse', ''),
            )
            from livreur.models import Livreur
            Livreur.objects.create(user=user)

            messages.success(
                request,
                f"Compte livreur créé : {user.prenom} {user.nom} — "
                f"identifiant {user.telephone}. Communiquez-lui ce numéro et le mot de passe choisi."
            )
            return redirect('admin_transformatrice:admin_livreurs')
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")

    livreurs = User.objects.filter(role=User.Role.LIVREUR).order_by('-date_joined')

    # Nombre de livraisons en cours / terminées par livreur (pour affichage)
    livreurs_stats = []
    for livreur in livreurs:
        livraisons_qs = Livraison.objects.filter(livreur=livreur)
        livreurs_stats.append({
            'user': livreur,
            'total_livraisons': livraisons_qs.count(),
            'en_cours': livraisons_qs.filter(confirme_le__isnull=True).count(),
        })

    context = {
        'active_nav': 'livreurs',
        'form': form,
        'livreurs_stats': livreurs_stats,
    }
    return render(request, 'espace_admin/livreurs.html', context)


# ============================================================
#  COMMANDES PADDY (suivi + changement de statut)
# ============================================================

@admin_required
def admin_commandes_paddy(request):
    """Liste de toutes les commandes paddy passées aux producteurs."""
    statut_filtre = request.GET.get('statut', 'toutes')

    qs = CommandePaddy.objects.select_related(
        'stock__producteur__user', 'commande_par'
    ).order_by('-cree_le')

    if statut_filtre != 'toutes':
        qs = qs.filter(statut=statut_filtre)

    counts = {s: CommandePaddy.objects.filter(statut=s).count() for s, _ in CommandePaddy.Statut.choices}
    total = CommandePaddy.objects.count()

    context = {
        'active_nav': 'stocks',
        'commandes': qs,
        'statut_filtre': statut_filtre,
        'total': total,
        'counts': counts,
        'status_tabs': [
            {'label': 'Toutes',      'value': 'toutes',     'count': total,                         'active': statut_filtre == 'toutes'},
            {'label': 'En attente',  'value': 'en_attente', 'count': counts.get('en_attente', 0),   'active': statut_filtre == 'en_attente'},
            {'label': 'Confirmée',   'value': 'confirmee',  'count': counts.get('confirmee', 0),    'active': statut_filtre == 'confirmee'},
            {'label': 'Reçue',       'value': 'recue',      'count': counts.get('recue', 0),        'active': statut_filtre == 'recue'},
            {'label': 'Annulée',     'value': 'annulee',    'count': counts.get('annulee', 0),      'active': statut_filtre == 'annulee'},
        ],
    }
    return render(request, 'espace_admin/commandes_paddy.html', context)


@admin_required
def admin_commande_paddy_statut(request, pk):
    """Met à jour le statut d'une commande paddy."""
    if request.method == 'POST':
        commande = get_object_or_404(CommandePaddy, pk=pk)
        nouveau_statut = request.POST.get('statut')
        statuts_valides = [s for s, _ in CommandePaddy.Statut.choices]

        if nouveau_statut in statuts_valides:
            commande.statut = nouveau_statut
            commande.save(update_fields=['statut'])

            if nouveau_statut == CommandePaddy.Statut.RECUE:
                messages.success(
                    request,
                    f"Commande #PAD-{pk:04d} marquée comme reçue. "
                    "Vous pouvez maintenant créer des produits depuis cette commande."
                )
            else:
                messages.success(request, f"Commande #PAD-{pk:04d} mise à jour.")

    return redirect('admin_transformatrice:admin_commandes_paddy')


# ============================================================
#  TÉLÉCHARGEMENT QR CODE (admin connecté)
# ============================================================

@admin_required
def admin_qr_download(request, lot_code):
    """Génère et télécharge le QR code d'un produit — encode l'URL de traçabilité."""
    get_object_or_404(Produit, code_lot=lot_code)
    tracabilite_url = request.build_absolute_uri(
        reverse('admin_transformatrice:tracabilite_produit', args=[lot_code])
    )
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(tracabilite_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a5c32", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    response = HttpResponse(buf.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="qr_{lot_code}.png"'
    return response


# ============================================================
#  TRAÇABILITÉ QR CODE (public — sans connexion)
# ============================================================

def tracabilite_produit(request, lot_code):
    """Page publique scannée via QR code — affiche l'origine du riz paddy."""
    produit = get_object_or_404(
        Produit.objects.select_related(
            'stock_source__stock__producteur__user',
            'stock_source__commande_par',
        ),
        code_lot=lot_code,
    )

    # Tous les formats (poids) issus du même lot et de la même commande paddy
    tous_formats = Produit.objects.filter(
        nom=produit.nom,
        stock_source=produit.stock_source,
    ).order_by('poids_kg')

    context = {
        'produit': produit,
        'lot_code': lot_code,
        'tous_formats': tous_formats,
    }
    return render(request, 'espace_admin/tracabilite.html', context)
