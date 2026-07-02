from django.db import models
from producteur.models import Produit


class Client(models.Model):
    """
    Pas de compte utilisateur : le client ne se connecte pas.
    Il faut l'enregistrer AVANT de créer une commande, pour récupérer sa clé (pk)
    à utiliser comme FK dans CommandeClient.
    """
    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    adresse = models.CharField(max_length=255, blank=True)

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

    def __str__(self):
        return f"Commande #{self.pk} - {self.client}"


class LigneCommande(models.Model):
    """
    Ajout non explicite dans le diagramme : relie une commande à ses produits.
    Sans ça, CommandeClient ne sait pas ce que le client a commandé.
    """
    commande = models.ForeignKey(CommandeClient, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name='lignes_commande')
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantite} x {self.produit.nom}"