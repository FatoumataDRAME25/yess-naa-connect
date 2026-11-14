"""
Gestion automatique du stock de sacs (Produit.stock_sacs) par les commandes clients.

Règles :
- Commande passée            → les sacs sont retirés du stock (réservés).
- Commande annulée           → les sacs reviennent au stock.
- Annulation levée           → les sacs sont de nouveau retirés (si le stock le permet).
- Commande livrée            → rien ne bouge : les sacs sont partis chez le client.
- Commande supprimée (archivée), non livrée → les sacs reviennent au stock ;
  restaurée depuis les archives → ils sont de nouveau retirés.

Seules les commandes passées depuis la mise en place (CommandeClient.gestion_stock)
sont concernées : les plus anciennes, qui n'avaient jamais retiré de sacs, ne
touchent jamais au stock. Chaque commande mémorise si elle détient une réservation
(CommandeClient.stock_reserve) : elle ne retire ou ne rend jamais deux fois ses sacs.

Toutes les fonctions doivent être appelées dans une transaction (transaction.atomic) :
les produits concernés sont verrouillés pour éviter de vendre deux fois le dernier sac.
"""
from collections import defaultdict

from django.db.models import F

from administration.models import Produit


class StockInsuffisant(Exception):
    def __init__(self, manques):
        # manques : liste de (produit, quantité demandée, quantité disponible)
        self.manques = manques
        super().__init__(self.message())

    def message(self):
        return " ; ".join(
            f"« {p.nom} » : {dispo} sac(s) disponible(s) pour {demande} demandé(s)"
            for p, demande, dispo in self.manques
        )


def _besoins(commande):
    besoins = defaultdict(int)
    for ligne in commande.lignes.all():
        besoins[ligne.produit_id] += ligne.quantite
    return besoins


def reserver_stock(commande):
    """Retire du stock les sacs de la commande. Lève StockInsuffisant si un produit manque."""
    if not commande.gestion_stock or commande.stock_reserve:
        return
    besoins = _besoins(commande)
    produits = {
        p.pk: p for p in Produit.objects.select_for_update().filter(pk__in=besoins)
    }
    manques = [
        (produits[pid], qte, produits[pid].stock_sacs)
        for pid, qte in besoins.items()
        if produits[pid].stock_sacs < qte
    ]
    if manques:
        raise StockInsuffisant(manques)
    for pid, qte in besoins.items():
        Produit.objects.filter(pk=pid).update(stock_sacs=F('stock_sacs') - qte)
    commande.stock_reserve = True
    commande.save(update_fields=['stock_reserve'])


def liberer_stock(commande):
    """Remet en stock les sacs réservés par la commande (sans effet s'il n'y en a pas)."""
    if not commande.gestion_stock or not commande.stock_reserve:
        return
    besoins = _besoins(commande)
    list(Produit.objects.select_for_update().filter(pk__in=besoins))  # verrou
    for pid, qte in besoins.items():
        Produit.objects.filter(pk=pid).update(stock_sacs=F('stock_sacs') + qte)
    commande.stock_reserve = False
    commande.save(update_fields=['stock_reserve'])


def changer_statut(commande, nouveau_statut):
    """
    Change le statut d'une commande en tenant le stock à jour.
    Lève StockInsuffisant si l'on rouvre une commande annulée sans stock suffisant
    (le statut n'est alors pas modifié).
    """
    Statut = type(commande).Statut
    ancien = commande.statut
    if nouveau_statut == ancien:
        return
    if nouveau_statut == Statut.ANNULEE:
        liberer_stock(commande)
    elif ancien == Statut.ANNULEE:
        reserver_stock(commande)
    commande.statut = nouveau_statut
    commande.save(update_fields=['statut'])
