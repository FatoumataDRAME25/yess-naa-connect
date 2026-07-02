from django.db import models
from django.utils.crypto import get_random_string

from administration.models import Produit


def _generer_numero_commande():
    """Génère un numéro de commande unique lisible ex: YEES-2026-A3F7."""
    from django.utils import timezone
    annee = timezone.now().year
    code = get_random_string(4, 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789')
    return f"YEES-{annee}-{code}"


class Client(models.Model):
    """
    Le client ne se connecte pas — il est enregistré avant toute commande
    pour servir de clé étrangère dans CommandeClient.
    """
    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    adresse = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.telephone})"


class CommandeClient(models.Model):
    class Statut(models.TextChoices):
        ATTENTE      = 'attente',      'En attente'
        PREPARATION  = 'preparation',  'En préparation'
        EN_LIVRAISON = 'en_livraison', 'En livraison'
        LIVREE       = 'livree',       'Livrée'
        ANNULEE      = 'annulee',      'Annulée'

    numero          = models.CharField(max_length=20, unique=True, blank=True)
    client          = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='commandes')
    statut          = models.CharField(max_length=20, choices=Statut.choices, default=Statut.ATTENTE)
    mode_paiement   = models.CharField(max_length=50)
    adresse_livraison = models.CharField(max_length=255, blank=True)
    frais_livraison = models.PositiveIntegerField(default=2000)
    date            = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Commande client'
        verbose_name_plural = 'Commandes clients'
        ordering = ['-date']

    def save(self, *args, **kwargs):
        if not self.numero:
            # Boucle pour garantir l'unicité
            numero = _generer_numero_commande()
            while CommandeClient.objects.filter(numero=numero).exists():
                numero = _generer_numero_commande()
            self.numero = numero
        super().save(*args, **kwargs)

    @property
    def sous_total(self):
        return sum(l.quantite * l.prix_unitaire for l in self.lignes.all())

    @property
    def total(self):
        return self.sous_total + self.frais_livraison

    def __str__(self):
        return f"Commande {self.numero} — {self.client}"


class LigneCommande(models.Model):
    """Relie une commande client à ses produits avec quantité et prix."""
    commande      = models.ForeignKey(CommandeClient, on_delete=models.CASCADE, related_name='lignes')
    produit       = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name='lignes_commande')
    quantite      = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Ligne de commande'
        verbose_name_plural = 'Lignes de commande'

    @property
    def ligne_total(self):
        return self.quantite * self.prix_unitaire

    def __str__(self):
        return f"{self.quantite} × {self.produit.nom} ({self.produit.poids_kg} kg)"
