from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date, datetime
from urllib.parse import quote
import random

# from .models import Produit  # modèles en cours de refonte


# ============================================================
#  AUTHENTIFICATION
# ============================================================

def admin_login(request):
    """Connexion de la transformatrice/admin."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('admin_transformatrice:admin_dashboard')
        messages.error(request, "Identifiant ou mot de passe incorrect.")
        return render(request, 'espace_admin/login.html', {'form': {'errors': True}})
    return render(request, 'espace_admin/login.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_transformatrice:admin_login')


# ============================================================
#  TABLEAU DE BORD
# ============================================================

@login_required(login_url='/espace-admin/connexion/')
def admin_dashboard(request):
    context = {
        'active_nav': 'dashboard',
        'today': date.today(),
        'stats': {
            'commandes_jour': 8,
            'ca_mois': '850 000',
            'stock_paddy': '2 500',
            'producteurs_actifs': 18,
        },
        'ventes_semaine': [45000, 52000, 38000, 64000, 47000, 69000, 58000],
        'pct_livraison': 65,
        'pct_en_ligne': 35,
        'commandes_recentes': _get_dummy_commandes()[:4],
    }
    return render(request, 'espace_admin/dashboard.html', context)


# ============================================================
#  STOCKS PRODUCTEURS
# ============================================================

@login_required(login_url='/espace-admin/connexion/')
def admin_stocks(request):
    commande_envoyee = request.session.pop('commande_envoyee', None)
    context = {
        'active_nav': 'stocks',
        'stock_total_kg': '2 500',
        'nb_producteurs': 18,
        'regions': ['Saint-Louis', 'Casamance', 'Thiès', 'Mbour'],
        'varietes': ['Sahel 108', 'Nerica'],
        'stocks_producteurs': _get_dummy_stocks(),
        'commande_envoyee': commande_envoyee,
    }
    return render(request, 'espace_admin/stocks_producteurs.html', context)


@login_required(login_url='/espace-admin/connexion/')
def admin_commander_paddy(request):
    if request.method == 'POST':
        quantite_kg = request.POST.get('quantite_kg', '0')
        date_livraison = request.POST.get('date_livraison', '')
        prix_kg = request.POST.get('prix_kg', '0')
        producteur_nom = request.POST.get('producteur_nom', '')

        try:
            total = int(quantite_kg) * int(prix_kg)
            total_fmt = f"{total:,}".replace(',', ' ')
        except (ValueError, TypeError):
            total_fmt = '0'

        if date_livraison:
            try:
                date_fmt = datetime.strptime(date_livraison, '%Y-%m-%d').strftime('%d/%m/%Y')
            except ValueError:
                date_fmt = date_livraison
        else:
            date_fmt = ''

        request.session['commande_envoyee'] = {
            'producteur_nom': producteur_nom,
            'quantite_kg': quantite_kg,
            'date_livraison': date_fmt,
            'total': total_fmt,
            'reference': f"#PAD-{date.today().year}-{random.randint(100, 9999):04d}",
        }
    return redirect('admin_transformatrice:admin_stocks')


# ============================================================
#  CATALOGUE
# ============================================================

@login_required(login_url='/espace-admin/connexion/')
def admin_catalogue(request):
    produit_publie = request.session.pop('produit_publie', None)
    filtre = request.GET.get('filtre', 'tous')

    tous_produits = Produit.objects.all()

    if filtre == 'en_ligne':
        produits_affiches = tous_produits.filter(statut='en_ligne')
    elif filtre == 'rupture':
        produits_affiches = tous_produits.filter(statut__in=('rupture', 'stock_faible'))
    else:
        produits_affiches = tous_produits

    produits_stock_faible = tous_produits.filter(statut='stock_faible')
    total = tous_produits.count()

    context = {
        'active_nav': 'catalogue',
        'produits': produits_affiches,
        'tous_produits_count': total,
        'en_ligne_count': tous_produits.filter(statut='en_ligne').count(),
        'rupture_count': tous_produits.filter(statut__in=('rupture', 'stock_faible')).count(),
        'produits_stock_faible': produits_stock_faible,
        'variantes_poids': ['5 kg', '10 kg', '25 kg'],
        'produit_publie': produit_publie,
        'filtre_actif': filtre,
    }
    return render(request, 'espace_admin/catalogue.html', context)


@login_required(login_url='/espace-admin/connexion/')
def admin_produit_create(request):
    if request.method == 'POST':
        nom          = request.POST.get('nom', '').strip()
        type_riz     = request.POST.get('type_riz', 'blanc')
        description  = request.POST.get('description', '')
        stock_initial = int(request.POST.get('stock_initial') or 0)
        generer_qr   = request.POST.get('generer_qr') == 'on'
        photo        = request.FILES.get('photo')

        # Récupère les variantes cochées et leur prix
        variantes = request.POST.getlist('variantes')

        if not nom:
            messages.error(request, "Le nom du produit est obligatoire.")
            return redirect('admin_transformatrice:admin_catalogue')

        lot_code = f"LOT-YN-{date.today().year}-{random.randint(1000, 9999):04d}" if generer_qr else ''

        # Crée un produit par variante cochée
        produits_crees = []
        if variantes:
            for poids in variantes:
                prix_val = request.POST.get(f'prix_{poids}', '0') or '0'
                try:
                    prix = int(float(prix_val))
                except ValueError:
                    prix = 0

                p = Produit.objects.create(
                    nom=nom,
                    type_riz=type_riz,
                    format=poids,
                    prix=prix,
                    stock_sacs=stock_initial,
                    description=description,
                    photo=photo if photo else None,
                    lot_code=lot_code,
                    generer_qr=generer_qr,
                )
                produits_crees.append(p.format)
        else:
            # Pas de variante cochée → on crée quand même avec les données de base
            prix_val = request.POST.get('prix_5 kg') or request.POST.get('prix_10 kg') or '0'
            try:
                prix = int(float(prix_val))
            except ValueError:
                prix = 0
            p = Produit.objects.create(
                nom=nom,
                type_riz=type_riz,
                format='—',
                prix=prix,
                stock_sacs=stock_initial,
                description=description,
                photo=photo if photo else None,
                lot_code=lot_code,
                generer_qr=generer_qr,
            )
            produits_crees.append('—')

        request.session['produit_publie'] = {
            'nom': nom,
            'variantes': produits_crees,
            'lot_code': lot_code,
            'qr_url': f"https://api.qrserver.com/v1/create-qr-code/?size=130x130&data={lot_code}" if lot_code else '',
        }
    return redirect('admin_transformatrice:admin_catalogue')


@login_required(login_url='/espace-admin/connexion/')
def admin_produit_edit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        if not nom:
            messages.error(request, "Le nom du produit est obligatoire.")
            return redirect('admin_transformatrice:admin_produit_edit', pk=pk)

        produit.nom         = nom
        produit.type_riz    = request.POST.get('type_riz', produit.type_riz)
        produit.format      = request.POST.get('format', produit.format)
        produit.description = request.POST.get('description', produit.description)
        try:
            produit.prix       = int(float(request.POST.get('prix', produit.prix)))
            produit.stock_sacs = int(request.POST.get('stock_sacs', produit.stock_sacs))
        except (ValueError, TypeError):
            messages.error(request, "Prix ou stock invalide.")
            return redirect('admin_transformatrice:admin_produit_edit', pk=pk)
        if request.FILES.get('photo'):
            produit.photo = request.FILES['photo']
        produit.save()
        messages.success(request, "Produit mis à jour.")
        return redirect('admin_transformatrice:admin_catalogue')

    context = {
        'active_nav': 'catalogue',
        'produit': produit,
        'variantes_poids': _get_formats_produit(produit),
        'type_riz_choices': Produit.TYPE_CHOIX,
    }
    return render(request, 'espace_admin/catalogue_edit.html', context)


@login_required(login_url='/espace-admin/connexion/')
def admin_produit_delete(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        produit.delete()
        messages.success(request, "Produit supprimé.")
    return redirect('admin_transformatrice:admin_catalogue')


# ============================================================
#  COMMANDES CLIENTS
# ============================================================

@login_required(login_url='/espace-admin/connexion/')
def admin_commandes(request):
    statut_filtre = request.GET.get('statut', 'toutes')
    commandes = _get_dummy_commandes()

    if statut_filtre != 'toutes':
        commandes = [c for c in commandes if c['statut'] == statut_filtre]

    context = {
        'active_nav': 'commandes',
        'stats': {
            'total': '1,248',
            'en_attente': 45,
            'en_livraison': 18,
            'revenu_jour': '845k',
        },
        'status_tabs': [
            {'label': 'Toutes', 'value': 'toutes', 'count': 1248, 'active': statut_filtre == 'toutes'},
            {'label': 'En attente', 'value': 'en_attente', 'count': 45, 'active': statut_filtre == 'en_attente'},
            {'label': 'En préparation', 'value': 'en_preparation', 'count': 23, 'active': statut_filtre == 'en_preparation'},
            {'label': 'En livraison', 'value': 'en_livraison', 'count': 18, 'active': statut_filtre == 'en_livraison'},
            {'label': 'Livrée', 'value': 'livree', 'count': 1142, 'active': statut_filtre == 'livree'},
            {'label': 'Annulée', 'value': 'annulee', 'count': 20, 'active': statut_filtre == 'annulee'},
        ],
        'commandes': commandes,
    }
    return render(request, 'espace_admin/commandes.html', context)


@login_required(login_url='/espace-admin/connexion/')
def admin_commande_detail(request, pk):
    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')
        messages.success(request, f"Commande #{pk} mise à jour.")
        return redirect('admin_transformatrice:admin_commandes')

    commande = _get_dummy_commande_detail(pk)
    etapes = [
        {'label': 'Marquer en préparation', 'value': 'en_preparation',
         'active': commande['statut'] == 'en_attente'},
        {'label': 'Marquer en livraison', 'value': 'en_livraison',
         'active': commande['statut'] == 'en_preparation'},
        {'label': 'Marquer livrée', 'value': 'livree',
         'active': commande['statut'] == 'en_livraison'},
    ]

    statut = commande['statut']
    stepper_steps = [
        ('Attente',    statut in ('en_preparation', 'en_livraison', 'livree')),
        ('Préparation', statut in ('en_livraison', 'livree')),
        ('Livraison',  statut in ('en_livraison', 'livree')),
        ('Livrée',     statut == 'livree'),
    ]

    context = {
        'active_nav': 'commandes',
        'commande': commande,
        'etapes': etapes,
        'stepper_steps': stepper_steps,
    }
    return render(request, 'espace_admin/commande_detail.html', context)


@login_required(login_url='/espace-admin/connexion/')
def admin_about(request):
    context = {'active_nav': 'about'}
    return render(request, 'espace_admin/about.html', context)


# ============================================================
#  TRAÇABILITÉ QR CODE (public — accessible sans connexion)
# ============================================================

def tracabilite_produit(request, lot_code):
    """Page publique scannée via QR code — affiche les infos du produit."""
    produits = Produit.objects.filter(lot_code=lot_code)
    if not produits.exists():
        return render(request, 'espace_admin/tracabilite_introuvable.html', {'lot_code': lot_code}, status=404)

    produit = produits.first()
    context = {
        'produit': produit,
        'lot_code': lot_code,
        'tous_formats': produits,  # toutes les variantes du même lot
    }
    return render(request, 'espace_admin/tracabilite.html', context)


# ============================================================
#  DONNÉES FACTICES — à supprimer une fois les models branchés
# ============================================================

def _get_formats_produit(produit=None):
    formats = ['5 kg', '10 kg', '25 kg']
    if produit and produit.format and produit.format not in formats:
        formats = [produit.format] + formats
    return formats


def _get_dummy_commande_detail(pk):
    mois_fr = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
               'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    base = next((c for c in _get_dummy_commandes() if c['id'] == pk), _get_dummy_commandes()[0])
    d = base['date']
    statut_labels = {
        'en_attente': 'En attente', 'en_preparation': 'En préparation',
        'en_livraison': 'En livraison', 'livree': 'Livrée', 'annulee': 'Annulée',
    }
    return {
        **base,
        'numero': f"YEES-{pk:03d}",
        'date_str': f"{d.day} {mois_fr[d.month]} {d.year}",
        'heure': '10:45',
        'statut_label': statut_labels.get(base['statut'], base['statut']),
        'client': {
            'nom': base['client_nom'],
            'telephone': base['client_telephone'],
            'email': f"{base['client_nom'].lower().replace(' ', '.')}@email.com",
        },
        'adresse': {
            'ligne1': 'Cité Keur Gorgui, Immeuble Horizon',
            'ligne2': 'Appartement 4B, 3ème étage',
            'ville': 'Dakar, Sénégal',
            'maps_url': 'https://www.google.com/maps/search/?api=1&query=' + quote(
                'Cité Keur Gorgui, Immeuble Horizon, Appartement 4B, 3ème étage, Dakar, Sénégal'
            ),
        },
        'articles': [
            {
                'nom': 'Riz Blanc Premium 10kg',
                'photo_url': '/static/images/2sac10kg.jpg',
                'quantite': 2, 'prix_unitaire': '8 500', 'sous_total': '17 000',
            },
            {
                'nom': 'Riz Blanc Premium 5kg',
                'photo_url': '/static/images/2sac5kg.jpg',
                'quantite': 1, 'prix_unitaire': '4 500', 'sous_total': '4 500',
            },
        ],
        'sous_total': '21 500',
        'frais_livraison': '1 500',
        'total': '23 000',
        'qr_url': f'https://api.qrserver.com/v1/create-qr-code/?size=100x100&data=YEES-{pk:03d}',
    }

def _get_dummy_stocks():
    return [
        {
            'id': 1,
            'variete': 'Sahel 108',
            'photo_url': '/static/images/paddy1.jpeg',
            'producteur': {'nom': 'Moussa Diop', 'region': 'Ross Béthio, Saint-Louis',
                           'photo_url': '/static/images/agri1.jpg'},
            'quantite_kg': 450, 'prix_kg': 185,
            'date_recolte': date(2023, 10, 12),
        },
        {
            'id': 2,
            'variete': 'Nerica',
            'photo_url': '/static/images/riz-nerica-kolda-600x316.jpg',
            'producteur': {'nom': 'Fatou Sow', 'region': 'Podor, Saint-Louis',
                           'photo_url': '/static/images/qgri2.jpg'},
            'quantite_kg': 820, 'prix_kg': 190,
            'date_recolte': date(2023, 10, 5),
        },
        {
            'id': 3,
            'variete': 'Sahel 108',
            'photo_url': '/static/images/PADDY3.jpg',
            'producteur': {'nom': 'Amadou Ly', 'region': 'Sédhiou, Casamance',
                           'photo_url': '/static/images/agri3.jpg'},
            'quantite_kg': 310, 'prix_kg': 205,
            'date_recolte': date(2023, 10, 18),
        },
    ]


def _get_dummy_produits():
    return [
        {
            'id': 1,
            'nom': 'Riz Parfumé "Teranga"',
            'type_riz': 'Riz long grain',
            'format': '5 kg',
            'prix': '4 500',
            'stock_sacs': 42,
            'statut': 'en_ligne',
            'photo_url': '/static/images/1sac5kg.jpg',
        },
        {
            'id': 2,
            'nom': 'Riz Étuvé Nutrition+',
            'type_riz': 'Riz brun étuvé',
            'format': '10 kg',
            'prix': '8 750',
            'stock_sacs': 5,
            'statut': 'stock_faible',
            'photo_url': '/static/images/2sac10kg.jpg',
        },
        {
            'id': 3,
            'nom': 'Brisure de Riz (1/4)',
            'type_riz': 'Qualité supérieure',
            'format': '2 kg',
            'prix': '2 200',
            'stock_sacs': 0,
            'statut': 'rupture',
            'photo_url': '/static/images/3sac5kg.jpg',
        },
        {
            'id': 4,
            'nom': 'Riz Blanc Premium',
            'type_riz': 'Riz long grain',
            'format': '10 kg',
            'prix': '8 500',
            'stock_sacs': 78,
            'statut': 'en_ligne',
            'photo_url': '/static/images/1sac10kg.jpg',
        },
        {
            'id': 5,
            'nom': 'Riz Blanc Premium',
            'type_riz': 'Riz long grain',
            'format': '5 kg',
            'prix': '4 500',
            'stock_sacs': 34,
            'statut': 'en_ligne',
            'photo_url': '/static/images/2sac5kg.jpg',
        },
        {
            'id': 6,
            'nom': 'Riz Étuvé Classique',
            'type_riz': 'Riz brun étuvé',
            'format': '25 kg',
            'prix': '21 000',
            'stock_sacs': 12,
            'statut': 'en_ligne',
            'photo_url': '/static/images/4sac10kg.jpg',
        },
    ]


def _get_dummy_commandes():
    return [
        {'id': 1, 'numero': 'CMD-2024-001', 'client_nom': 'Moussa Diop', 'client_telephone': '+221 77 123 45 67',
         'produits_resume': 'Riz Blanc Premium 10kg × 2', 'montant': '17,000',
         'mode_paiement': 'livraison', 'statut': 'livree', 'date': date(2026, 6, 12), 'heure': '10:30',
         'client_photo': '/static/images/homme1.jpg'},
        {'id': 2, 'numero': 'CMD-2024-002', 'client_nom': 'Fatou Sow', 'client_telephone': '+221 78 987 65 43',
         'produits_resume': 'Riz Blanc Premium 5kg × 1', 'montant': '4,500',
         'mode_paiement': 'en_ligne', 'statut': 'en_preparation', 'date': date(2026, 6, 13), 'heure': '14:30',
         'client_photo': '/static/images/femme2.jpg'},
        {'id': 3, 'numero': 'CMD-2024-003', 'client_nom': 'Amadou Ba', 'client_telephone': '+221 70 555 12 34',
         'produits_resume': 'Riz Blanc Premium 10kg × 3', 'montant': '25,500',
         'mode_paiement': 'livraison', 'statut': 'en_livraison', 'date': date(2026, 6, 14), 'heure': '16:05',
         'client_photo': '/static/images/homme2.jpg'},
        {'id': 4, 'numero': 'CMD-2024-004', 'client_nom': 'Khadidiatou Sy', 'client_telephone': '+221 33 444 55 66',
         'produits_resume': 'Riz Blanc Premium 5kg × 2', 'montant': '9,000',
         'mode_paiement': 'en_ligne', 'statut': 'en_attente', 'date': date(2026, 6, 15), 'heure': '10:20',
         'client_photo': '/static/images/femme 1.jpg'},
    ]
