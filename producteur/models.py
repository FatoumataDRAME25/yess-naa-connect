from django.conf import settings
from django.db import models


class Producteur(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='producteur_profile'
    )

    def __str__(self):
        return f"Producteur: {self.user.prenom} {self.user.nom}"


class StockPaddy(models.Model):
    class Variete(models.TextChoices):
        BLANC = 'blanc', 'Blanc'
        PARFUME = 'parfume', 'Parfumé'

    class Statut(models.TextChoices):
        DISPONIBLE = 'disponible', 'Disponible'
        COMMANDE = 'commande', 'Commandé'
        EPUISE = 'epuise', 'Épuisé'

    producteur = models.ForeignKey(Producteur, on_delete=models.CASCADE, related_name='stocks')
    variete = models.CharField(max_length=20, choices=Variete.choices)
    quantite_kg = models.DecimalField(max_digits=10, decimal_places=2)
    prix_par_kg = models.DecimalField(max_digits=10, decimal_places=2)
    date_recolte = models.DateField()
    region = models.CharField(max_length=100)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.DISPONIBLE)
    est_bio = models.BooleanField(default=False)

    def __str__(self):
        return f"Stock #{self.pk} - {self.get_variete_display()} ({self.quantite_kg} kg)"


class CommandePaddy(models.Model):
    """Commande interne d'achat de paddy, passée par un admin sur un stock producteur."""
    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        CONFIRMEE = 'confirmee', 'Confirmée'
        RECUE = 'recue', 'Reçue'
        ANNULEE = 'annulee', 'Annulée'

    stock = models.ForeignKey(StockPaddy, on_delete=models.PROTECT, related_name='commandes_paddy')
    commande_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='commandes_paddy_passees'
    )
    quantite_commande = models.DecimalField(max_digits=10, decimal_places=2)
    date_livraison = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    cree_le = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CommandePaddy #{self.pk} - {self.stock}"


class Produit(models.Model):
    class TypeRiz(models.TextChoices):
        BLANC = 'blanc', 'Blanc'
        ETUVE = 'etuve', 'Étuvé'
        PARFUME = 'parfume', 'Parfumé'

    class Poids(models.IntegerChoices):
        CINQ = 5
        DIX = 10
        VINGT_CINQ = 25

    nom = models.CharField(max_length=150)
    type_riz = models.CharField(max_length=20, choices=TypeRiz.choices)
    poids_kg = models.PositiveSmallIntegerField(choices=Poids.choices)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    stock_sacs = models.PositiveIntegerField(default=0)
    code_lot = models.CharField(max_length=50, unique=True)
    est_actif = models.BooleanField(default=True)
    stock_source = models.ForeignKey(
        StockPaddy, on_delete=models.SET_NULL, null=True, blank=True, related_name='produits'
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} - {self.poids_kg}kg ({self.code_lot})"