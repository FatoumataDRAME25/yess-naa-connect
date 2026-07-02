from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Produit


# ---------------------------------------------------------------------------
# Helpers session panier
# Le panier est stocké en session sous la forme :
# request.session['panier'] = {
#     "produit_id": {
#         "nom": "...",
#         "prix": 5500,
#         "image": "/media/...",
#         "quantite": 2,
#         "poids": "5kg"
#     },
#     ...
# }
# ---------------------------------------------------------------------------

def get_panier(request):
    """Retourne le dict panier depuis la session (crée si absent)."""
    return request.session.get('panier', {})


def save_panier(request, panier):
    """Sauvegarde le panier dans la session et force la mise à jour."""
    request.session['panier'] = panier
    request.session.modified = True


def nb_articles_panier(request):
    """Nombre total d'articles dans le panier (somme des quantités)."""
    panier = get_panier(request)
    return sum(item['quantite'] for item in panier.values())


def total_panier(request):
    """Calcule le montant total du panier."""
    panier = get_panier(request)
    return sum(item['prix'] * item['quantite'] for item in panier.values())


# ---------------------------------------------------------------------------
# Pages principales
# ---------------------------------------------------------------------------

def accueil(request):
    produits = Produit.objects.filter(actif=True)[:4]
    context = {
        'produits': produits,
        'nb_panier': nb_articles_panier(request),
    }
    return render(request, "client/accueil.html", context)


def catalogue(request):
    # --- Paramètres de filtrage depuis l'URL (GET) ---
    # ex: /client/cat/?q=blanc&categorie=parfume&poids=5kg&page=2
    q         = request.GET.get('q', '').strip()
    categorie = request.GET.get('categorie', '')   # 'blanc','parfume','complet','brisure'
    poids     = request.GET.get('poids', '')       # '5kg','10kg','25kg'

    # --- Construction du queryset avec filtres cumulatifs ---
    produits = Produit.objects.filter(actif=True)

    if q:
        # Recherche insensible à la casse sur le nom
        produits = produits.filter(nom__icontains=q)

    if categorie:
        produits = produits.filter(categorie=categorie)

    if poids:
        # poids_options est une chaîne "5kg,10kg,25kg"
        # on cherche si le poids demandé apparaît dans cette chaîne
        produits = produits.filter(poids_options__icontains=poids)

    # --- Pagination : 8 produits par page ---
    from django.core.paginator import Paginator
    paginator  = Paginator(produits, 8)
    page_num   = request.GET.get('page', 1)
    page_obj   = paginator.get_page(page_num)

    # --- Si requête AJAX (bouton "Charger plus") ---
    # Le JS envoie un header X-Requested-With: XMLHttpRequest
    # On retourne seulement le fragment HTML des nouvelles cards
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        html = render_to_string(
            'client/partials/cards_produits.html',
            {'produits': page_obj, 'nb_panier': nb_articles_panier(request)},
            request=request
        )
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        })

    context = {
        'produits':       page_obj,
        'nb_panier':      nb_articles_panier(request),
        'has_next':       page_obj.has_next(),
        'next_page':      page_obj.next_page_number() if page_obj.has_next() else None,
        # On renvoie les filtres actifs pour que le template puisse
        # marquer le bon bouton comme actif
        'q':              q,
        'categorie_active': categorie,
        'poids_actif':    poids,
        # Liste des catégories disponibles pour générer les boutons
        'categories':     Produit.CATEGORIE_CHOICES,
    }
    return render(request, "client/catalogue.html", context)


def produit_detail(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id, actif=True)

    # Récupérer la quantité de ce produit déjà dans le panier
    panier = get_panier(request)
    qte_dans_panier = panier.get(str(produit_id), {}).get('quantite', 0)

    context = {
        'produit': produit,
        'nb_panier': nb_articles_panier(request),
        'qte_dans_panier': qte_dans_panier,
    }
    return render(request, "client/detailProduit.html", context)


def panier(request):
    panier_session = get_panier(request)
    articles = []
    sous_total = 0

    for produit_id, item in panier_session.items():
        ligne_total = item['prix'] * item['quantite']
        sous_total += ligne_total
        articles.append({
            'id': produit_id,
            'nom': item['nom'],
            'prix': item['prix'],
            'image': item.get('image', ''),
            'quantite': item['quantite'],
            'poids': item.get('poids', ''),
            'ligne_total': ligne_total,
        })

    frais_livraison = 2000 if articles else 0
    total = sous_total + frais_livraison

    context = {
        'articles': articles,
        'sous_total': sous_total,
        'frais_livraison': frais_livraison,
        'total': total,
        'nb_panier': nb_articles_panier(request),
        'panier_vide': len(articles) == 0,
    }
    return render(request, "client/panier.html", context)


def finaliser_commande(request):
    panier_session = get_panier(request)
    if not panier_session:
        return redirect('panier')

    articles = []
    sous_total = 0
    for produit_id, item in panier_session.items():
        ligne_total = item['prix'] * item['quantite']
        sous_total += ligne_total
        articles.append({
            'id': produit_id,
            'nom': item['nom'],
            'prix': item['prix'],
            'image': item.get('image', ''),
            'quantite': item['quantite'],
            'poids': item.get('poids', ''),
            'ligne_total': ligne_total,
        })

    frais_livraison = 2000
    total = sous_total + frais_livraison

    context = {
        'articles': articles,
        'sous_total': sous_total,
        'frais_livraison': frais_livraison,
        'total': total,
        'nb_panier': nb_articles_panier(request),
    }
    return render(request, "client/finaliser_commande.html", context)


def confirmer_commande(request):
    context = {
        'nb_panier': nb_articles_panier(request),
    }
    return render(request, "client/confirmation_commande.html", context)


def suivre_commande(request):
    context = {
        'nb_panier': nb_articles_panier(request),
    }
    return render(request, "client/suivre_commande.html", context)


# ---------------------------------------------------------------------------
# Actions panier (POST)
# ---------------------------------------------------------------------------

@require_POST
def ajouter_au_panier(request, produit_id):
    """Ajoute un produit au panier ou incrémente sa quantité."""
    produit = get_object_or_404(Produit, id=produit_id, actif=True)
    panier = get_panier(request)

    quantite = int(request.POST.get('quantite', 1))
    poids = request.POST.get('poids', produit.get_poids_liste()[0])

    cle = str(produit_id)

    if cle in panier:
        panier[cle]['quantite'] += quantite
    else:
        image_url = produit.image.url if produit.image else ''
        panier[cle] = {
            'nom': produit.nom,
            'prix': int(produit.prix),
            'image': image_url,
            'quantite': quantite,
            'poids': poids,
        }

    save_panier(request, panier)

    # Retourne JSON pour la mise à jour dynamique du badge
    nb = nb_articles_panier(request)
    return JsonResponse({'success': True, 'nb_panier': nb})


@require_POST
def modifier_quantite(request, produit_id):
    """Modifie la quantité d'un article dans le panier."""
    panier = get_panier(request)
    cle = str(produit_id)
    action = request.POST.get('action')  # 'increment' ou 'decrement'

    if cle in panier:
        if action == 'increment':
            panier[cle]['quantite'] += 1
        elif action == 'decrement':
            if panier[cle]['quantite'] > 1:
                panier[cle]['quantite'] -= 1
            else:
                del panier[cle]
        save_panier(request, panier)

    nb = nb_articles_panier(request)
    quantite = panier.get(cle, {}).get('quantite', 0)
    return JsonResponse({'success': True, 'nb_panier': nb, 'quantite': quantite})


@require_POST
def supprimer_du_panier(request, produit_id):
    """Supprime un article du panier."""
    panier = get_panier(request)
    cle = str(produit_id)

    if cle in panier:
        del panier[cle]
        save_panier(request, panier)

    nb = nb_articles_panier(request)
    return JsonResponse({'success': True, 'nb_panier': nb})


@require_POST
def vider_panier(request):
    """Vide complètement le panier."""
    save_panier(request, {})
    return JsonResponse({'success': True, 'nb_panier': 0})
