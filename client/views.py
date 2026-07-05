import base64
import io
import re

import qrcode
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.urls import reverse
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


def _normaliser_telephone(numero):
    """Garde uniquement les chiffres et compare sur les 9 derniers (format sénégalais)."""
    chiffres = re.sub(r'\D', '', numero or '')
    return chiffres[-9:] if len(chiffres) >= 9 else chiffres


# ---------------------------------------------------------------------------
# Pages principales
# ---------------------------------------------------------------------------

def a_propos(request):
    context = {
        'nb_panier': nb_articles_panier(request),
    }
    return render(request, "client/a_propos.html", context)


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

    tracabilite_url = request.build_absolute_uri(
        reverse('admin_transformatrice:tracabilite_produit', args=[produit.code_lot])
    )
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(tracabilite_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1a5c32", back_color="white")
    buf = io.BytesIO()
    qr_img.save(buf, format='PNG')
    qr_code_base64 = base64.b64encode(buf.getvalue()).decode()

    context = {
        'produit': produit,
        'nb_panier': nb_articles_panier(request),
        'qte_dans_panier': qte_dans_panier,
        'qr_code_base64': qr_code_base64,
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

    # Les frais de livraison dépendent de la distance et sont déterminés par
    # le livreur au moment de la remise, pas à la commande.
    total = sous_total

    context = {
        'articles': articles,
        'sous_total': sous_total,
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

    # Les frais de livraison dépendent de la distance et sont déterminés par
    # le livreur au moment de la remise, pas à la commande.
    total = sous_total

    if request.method == 'POST':
        nom            = request.POST.get('nom', '').strip()
        telephone      = request.POST.get('telephone', '').strip()
        adresse        = request.POST.get('adresse', '').strip()
        ville          = request.POST.get('ville', 'dakar').strip()
        mode_paiement  = request.POST.get('paiement', 'livraison').strip()
        latitude       = request.POST.get('latitude', '').strip()
        longitude      = request.POST.get('longitude', '').strip()

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
                'total': total,
                'form_nom': nom,
                'form_telephone': telephone,
                'form_adresse': adresse,
                'form_ville': ville,
                'form_paiement': mode_paiement,
                'form_latitude': latitude,
                'form_longitude': longitude,
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

        try:
            lat = float(latitude) if latitude else None
            lng = float(longitude) if longitude else None
        except ValueError:
            lat = lng = None

        commande = CommandeClient.objects.create(
            client=client,
            mode_paiement=mode_paiement,
            adresse_livraison=f"{adresse}, {ville}",
            latitude=lat,
            longitude=lng,
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

        # Commande enregistrée : on vide le panier et on garde une trace en
        # session pour autoriser le téléchargement du reçu sans re-saisie.
        save_panier(request, {})
        request.session['derniere_commande_numero'] = commande.numero

        context = {
            'commande': commande,
            'articles': articles,
            'sous_total': sous_total,
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

    # Les frais de livraison dépendent de la distance et sont déterminés par
    # le livreur au moment de la remise, pas à la commande.
    total = sous_total

    context = {
        'nb_panier': nb_articles_panier(request),
        'articles': articles,
        'sous_total': sous_total,
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
    numero = request.GET.get('numero', '').strip()
    telephone = request.GET.get('telephone', '').strip()

    commande = None
    erreur = None
    a_recherche = bool(numero or telephone)

    if a_recherche:
        if not numero or not telephone:
            erreur = "Veuillez renseigner le numéro de commande et le numéro de téléphone."
        else:
            candidate = (
                CommandeClient.objects
                .select_related('client')
                .prefetch_related('lignes__produit')
                .filter(numero__iexact=numero)
                .first()
            )
            if candidate and _normaliser_telephone(candidate.client.telephone) == _normaliser_telephone(telephone):
                commande = candidate
            else:
                erreur = "Aucune commande trouvée avec ces informations. Vérifiez le numéro de commande et le téléphone."

    etapes = None
    if commande and commande.statut != CommandeClient.Statut.ANNULEE:
        ordre = [
            CommandeClient.Statut.ATTENTE,
            CommandeClient.Statut.PREPARATION,
            CommandeClient.Statut.EN_LIVRAISON,
            CommandeClient.Statut.LIVREE,
        ]
        index_actuel = ordre.index(commande.statut)
        definitions = [
            ("Commande confirmée", "Votre commande a été validée et enregistrée avec succès."),
            ("En préparation", "Notre équipe sélectionne les meilleurs produits de nos producteurs locaux pour votre colis."),
            ("En livraison", "Votre colis a été confié à notre livreur pour la remise en main propre."),
            ("Livrée", "Le colis est arrivé à destination. Bon appétit !"),
        ]
        etapes = []
        for i, (titre, description) in enumerate(definitions):
            if i < index_actuel:
                statut_etape = 'complete'
            elif i == index_actuel:
                statut_etape = 'en_cours'
            else:
                statut_etape = 'attente'
            etapes.append({'titre': titre, 'description': description, 'statut': statut_etape})

    context = {
        'nb_panier': nb_articles_panier(request),
        'a_recherche': a_recherche,
        'numero_recherche': numero,
        'telephone_recherche': telephone,
        'commande': commande,
        'erreur': erreur,
        'etapes': etapes,
    }
    return render(request, "client/suivre_commande.html", context)


def recu_commande(request, numero):
    """Reçu / bon de commande imprimable — accessible sans compte.

    Autorisé si la session est celle qui vient de créer la commande, ou si
    le téléphone du client est fourni en paramètre (retour depuis le suivi).
    """
    commande = get_object_or_404(
        CommandeClient.objects.select_related('client').prefetch_related('lignes__produit'),
        numero__iexact=numero,
    )

    telephone = request.GET.get('telephone', '').strip()
    autorise = request.session.get('derniere_commande_numero') == commande.numero or (
        telephone and _normaliser_telephone(telephone) == _normaliser_telephone(commande.client.telephone)
    )
    if not autorise:
        raise Http404("Reçu introuvable.")

    context = {
        'commande': commande,
        'lignes': commande.lignes.select_related('produit').all(),
    }
    return render(request, "client/recu_commande.html", context)


def verification_qrcode(request):
    """Vérification de l'authenticité d'un produit via son code de lot réel."""
    code = request.GET.get('code', '').strip().upper()
    erreur = None

    if code:
        produit = Produit.objects.filter(code_lot__iexact=code).first()
        if produit:
            return redirect('admin_transformatrice:tracabilite_produit', lot_code=produit.code_lot)
        erreur = "Aucun produit trouvé avec ce code. Vérifiez le code inscrit sur le sceau de votre emballage."

    context = {
        'nb_panier': nb_articles_panier(request),
        'code_recherche': code,
        'erreur': erreur,
    }
    return render(request, "client/verification_qrcode.html", context)


def page_404(request, exception=None):
    context = {'nb_panier': nb_articles_panier(request)}
    return render(request, '404.html', context, status=404)