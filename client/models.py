from django.db import models

from administration.models import Produit


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
        ATTENTE = 'attente', 'En attente'
        PREPARATION = 'preparation', 'En préparation'
        EN_LIVRAISON = 'en_livraison', 'En livraison'
        LIVREE = 'livree', 'Livrée'
        ANNULEE = 'annulee', 'Annulée'

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='commandes')
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.ATTENTE)
    mode_paiement = models.CharField(max_length=50)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Commande client'
        verbose_name_plural = 'Commandes clients'
        ordering = ['-date']

    def __str__(self):
        return f"Commande #{self.pk} — {self.client}"

    @property
    def numero(self):
        return f"YEES-{self.pk:03d}"

    @property
    def client_nom(self):
        return f"{self.client.prenom} {self.client.nom}"

    @property
    def client_telephone(self):
        return self.client.telephone

    @property
    def montant(self):
        total = sum(l.quantite * l.prix_unitaire for l in self.lignes.all())
        return f"{int(total):,}".replace(",", " ")

    @property
    def produits_resume(self):
        return ", ".join(
            f"{l.quantite}× {l.produit.nom} {l.produit.poids_kg}kg"
            for l in self.lignes.all()
        )


class LigneCommande(models.Model):
    """Relie une commande client à ses produits avec quantité et prix."""
    commande = models.ForeignKey(CommandeClient, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name='lignes_commande')
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Ligne de commande'
        verbose_name_plural = 'Lignes de commande'

    def __str__(self):
        return f"{self.quantite} × {self.produit.nom} ({self.produit.poids_kg} kg)"
