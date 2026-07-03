from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from administration.models import Produit
from .models import Client, CommandeClient, LigneCommande
from django.core.paginator import Paginator
from django.template.loader import render_to_string


# ---------------------------------------------------------------------------
# Helpers session panier
# ---------------------------------------------------------------------------

def get_panier(request):
    """Retourne le panier stocké en session."""
    return request.session.get('panier', {})


def save_panier(request, panier):
    """Sauvegarde le panier dans la session."""
    request.session['panier'] = panier
    request.session.modified = True


#def nb_articles_panier(request):
    #"""Retourne le nombre total d'articles dans le panier."""
    #panier = get_panier(request)
    #return sum(item['quantite'] for item in panier.values())

def nb_articles_panier(request):
    """Retourne le nombre de produits DIFFÉRENTS dans le panier."""
    panier = get_panier(request)
    return len(panier)


def total_panier(request):
    """Calcule le total du panier."""
    panier = get_panier(request)
    return sum(item['prix'] * item['quantite'] for item in panier.values())


# ---------------------------------------------------------------------------
# Pages principales
# ---------------------------------------------------------------------------

def accueil(request):
    produits = Produit.objects.filter(est_actif=True)[:4]
    context = {
        'produits': produits,
        'nb_panier': nb_articles_panier(request),
    }
    return render(request, "client/accueil.html", context)


def catalogue(request):
    q        = request.GET.get('q', '').strip()
    type_riz = request.GET.get('type_riz', '')
    poids    = request.GET.get('poids', '')

    produits = Produit.objects.filter(est_actif=True)

    if q:
        produits = produits.filter(nom__icontains=q)
    if type_riz:
        produits = produits.filter(type_riz=type_riz)
    if poids:
        produits = produits.filter(poids_kg=poids)
    paginator = Paginator(produits, 8)
    page_num  = request.GET.get('page', 1)
    page_obj  = paginator.get_page(page_num)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
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
        'q':              q,
        'type_riz_actif': type_riz,
        'poids_actif':    poids,
        'types_riz':      Produit.TypeRiz.choices,
    }
    return render(request, "client/catalogue.html", context)


def produit_detail(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id, est_actif=True)
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


# ---------------------------------------------------------------------------
# Actions panier (POST)
# ---------------------------------------------------------------------------

@require_POST
def ajouter_au_panier(request, produit_id):
    produit  = get_object_or_404(Produit, id=produit_id, est_actif=True)
    panier   = get_panier(request)
    quantite = int(request.POST.get('quantite', 1))
    cle      = str(produit_id)

    if cle in panier:
        panier[cle]['quantite'] += quantite
    else:
        panier[cle] = {
            'nom':      produit.nom,
            'prix':     int(produit.prix),
            'image':    produit.photo.url if produit.photo else '',
            'quantite': quantite,
            'poids':    produit.poids_kg,
        }

    save_panier(request, panier)
    return JsonResponse({'success': True, 'nb_panier': nb_articles_panier(request)})


@require_POST
def modifier_quantite(request, produit_id):
    panier  = get_panier(request)
    cle     = str(produit_id)
    action  = request.POST.get('action')

    if cle in panier:
        if action == 'increment':
            panier[cle]['quantite'] += 1
        elif action == 'decrement':
            if panier[cle]['quantite'] > 1:
                panier[cle]['quantite'] -= 1
            else:
                del panier[cle]
        save_panier(request, panier)

    nb       = nb_articles_panier(request)
    quantite = panier.get(cle, {}).get('quantite', 0)
    return JsonResponse({'success': True, 'nb_panier': nb, 'quantite': quantite})


@require_POST
def supprimer_du_panier(request, produit_id):
    panier = get_panier(request)
    cle    = str(produit_id)
    if cle in panier:
        del panier[cle]
        save_panier(request, panier)
    return JsonResponse({'success': True, 'nb_panier': nb_articles_panier(request)})


@require_POST
def vider_panier(request):
    save_panier(request, {})
    return JsonResponse({'success': True, 'nb_panier': 0})



# ---------------------------------------------------------------------------
# Pages principales
# ---------------------------------------------------------------------------


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

    if request.method == 'POST':
        nom            = request.POST.get('nom', '').strip()
        telephone      = request.POST.get('telephone', '').strip()
        adresse        = request.POST.get('adresse', '').strip()
        ville          = request.POST.get('ville', 'dakar').strip()
        mode_paiement  = request.POST.get('mode_paiement', 'livraison').strip()

        erreurs = {}
        if not nom:
            erreurs['nom'] = "Le nom est obligatoire."
        if not telephone:
            erreurs['telephone'] = "Le téléphone est obligatoire."
        elif len(telephone) < 9:
            erreurs['telephone'] = "Numéro de téléphone invalide."
        if not adresse:
            erreurs['adresse'] = "L'adresse de livraison est obligatoire."

        if erreurs:
            # Retour au formulaire avec les erreurs et les valeurs saisies
            context = {
                'nb_panier': nb_articles_panier(request),
                'articles': articles,
                'sous_total': sous_total,
                'frais_livraison': frais_livraison,
                'total': total,
                'form_nom': nom,
                'form_telephone': telephone,
                'form_adresse': adresse,
                'form_ville': ville,
                'form_paiement': mode_paiement,
                'erreurs': erreurs,
            }
            return render(request, "client/finalisercommande.html", context)

        # --- Aucune erreur : on enregistre la commande ---
        parts = nom.split(' ', 1)
        prenom = parts[0]
        nom_famille = parts[1] if len(parts) > 1 else ''

        client = Client.objects.create(
            prenom=prenom,
            nom=nom_famille,
            telephone=telephone,
            adresse=f"{adresse}, {ville}",
        )

        commande = CommandeClient.objects.create(
            client=client,
            mode_paiement=mode_paiement,
            adresse_livraison=f"{adresse}, {ville}",
            frais_livraison=frais_livraison,
        )

        for produit_id, item in panier_session.items():
            produit = get_object_or_404(Produit, id=produit_id)

            LigneCommande.objects.create(
                commande=commande,
                produit=produit,
                quantite=item['quantite'],
                prix_unitaire=item['prix'],
            )

            # Décrément du stock — adapte le nom du champ si différent
            if hasattr(produit, 'stock'):
                produit.stock = max(0, produit.stock - item['quantite'])
                produit.save(update_fields=['stock'])

        # Commande enregistrée : on vide le panier
        save_panier(request, {})

        context = {
            'commande': commande,
            'articles': articles,
            'sous_total': sous_total,
            'frais_livraison': frais_livraison,
            'total': total,
            'nb_panier': 0,
        }
        return render(request, "client/confirmation_commande.html", context)

    # --- GET : pas de données de formulaire, on renvoie vers la page de saisie ---
    return redirect('confirmationCommande')


def confirmer_commande(request):
    panier_session = get_panier(request)

    # --- Articles + totaux du panier (pour l'affichage du récapitulatif) ---
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
        'nb_panier': nb_articles_panier(request),
        'articles': articles,
        'sous_total': sous_total,
        'frais_livraison': frais_livraison,
        'total': total,
        'form_nom': '',
        'form_telephone': '',
        'form_adresse': '',
        'form_ville': 'dakar',
        'form_paiement': 'livraison',
        'erreurs': {},
    }
    return render(request, "client/finalisercommande.html", context)


def suivre_commande(request):
    context = {
        'nb_panier': nb_articles_panier(request),
    }
    return render(request, "client/suivre_commande.html", context)