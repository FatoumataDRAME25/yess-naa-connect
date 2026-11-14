import uuid

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.conf import settings
from django.templatetags.static import static

from producteur.models import StockPaddy


# Photo par défaut de chaque type de riz (static/images/produits/<type>.jpg).
# Utilisée quand un produit n'a pas de photo propre. Pour couvrir un nouveau
# type, ajouter le fichier image puis la clé correspondante ici.
PHOTOS_PAR_TYPE = {
    'entier':    'images/produits/entier.jpg',
    'brise':     'images/produits/brise.jpg',
    'extra_fin': 'images/produits/extra_fin.jpg',
    'basmati':   'images/produits/basmati.jpg',
}


def _generer_code_lot():
    return f"RIZ-{uuid.uuid4().hex[:8].upper()}"


class CustomUserManager(UserManager):

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('prenom', 'Super')
        extra_fields.setdefault('nom', 'Admin')
        extra_fields.setdefault('telephone', '0000000000')
        extra_fields.setdefault('role', 'admin')
        return super().create_superuser(username, email, password, **extra_fields)

    def create_producteur(self, username, password, **extra_fields):
        extra_fields['role'] = User.Role.PRODUCTEUR
        return self.create_user(username, password=password, **extra_fields)

    def create_livreur(self, username, password, **extra_fields):
        extra_fields['role'] = User.Role.LIVREUR
        return self.create_user(username, password=password, **extra_fields)

    def create_admin_role(self, username, password, **extra_fields):
        extra_fields['role'] = User.Role.ADMIN
        return self.create_user(username, password=password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        PRODUCTEUR = 'producteur', 'Producteur'
        LIVREUR = 'livreur', 'Livreur'
        ADMIN = 'admin', 'Administrateur'

    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    role = models.CharField(max_length=20, choices=Role.choices)
    photo = models.ImageField(upload_to='users/photos/', blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True)

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.get_role_display()})"


class CommandePaddy(models.Model):
    """Commande interne d'achat de paddy, passée par un admin sur un stock producteur."""

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        CONFIRMEE = 'confirmee', 'Confirmée'
        RECUE = 'recue', 'Reçue'
        ANNULEE = 'annulee', 'Annulée'

    stock = models.ForeignKey(
        StockPaddy, on_delete=models.PROTECT, related_name='commandes_paddy'
    )
    commande_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='commandes_paddy_passees',
    )
    quantite_commande = models.DecimalField(max_digits=10, decimal_places=2)
    date_livraison = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    statut = models.CharField(
        max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Commande paddy'
        verbose_name_plural = 'Commandes paddy'
        ordering = ['-cree_le']

    def __str__(self):
        return f"Commande #{self.pk} — {self.stock.get_variete_display()} ({self.quantite_commande} kg)"


class RegleRemise(models.Model):
    """
    Règle de remise volume configurable par l'admin.
    Si le poids total commandé >= seuil_kg, on applique taux_remise % sur le sous-total.
    """
    seuil_kg    = models.PositiveIntegerField(
        default=1000,
        help_text="Quantité minimale en kg pour déclencher la remise (ex: 1000 pour 1 tonne)"
    )
    taux_remise = models.DecimalField(
        max_digits=5, decimal_places=2, default=15.00,
        help_text="Taux de remise en pourcentage (ex: 15.00 pour 15%)"
    )
    est_active  = models.BooleanField(default=True)
    description = models.CharField(max_length=255, blank=True,
        help_text="Description affichée au client (ex: Remise volume 3 tonnes)")

    class Meta:
        verbose_name = "Règle de remise"
        verbose_name_plural = "Règles de remise"
        ordering = ['-seuil_kg']

    def __str__(self):
        taux = f"{self.taux_remise:.2f}".rstrip('0').rstrip('.')
        return f"Remise volume {taux} % dès {self.seuil_kg} kg"


class Produit(models.Model):

    class TypeRiz(models.TextChoices):
        BLANC      = 'blanc',      'Riz Blanc'
        ETUVE      = 'etuve',      'Riz Étuvé'
        PARFUME    = 'parfume',    'Riz Parfumé'
        BRISE      = 'brise',      'Riz Brisé'
        ENTIER     = 'entier',     'Riz Entier'
        JASMINE    = 'jasmine',    'Riz Aromatisé (Jasmine)'
        EXTRA_FIN  = 'extra_fin',  'Riz Extra Fin'
        BASMATI    = 'basmati',    'Riz Basmati'

    class Poids(models.IntegerChoices):
        CINQ = 5, '5 kg'
        DIX = 10, '10 kg'
        VINGT_CINQ = 25, '25 kg'

    class Statut(models.TextChoices):
        EN_LIGNE = 'en_ligne', 'En ligne'
        RUPTURE = 'rupture', 'Rupture de stock'
        ARCHIVE = 'archive', 'Archivé'

    nom = models.CharField(max_length=150)
    type_riz = models.CharField(max_length=20, choices=TypeRiz.choices)
    poids_kg = models.PositiveSmallIntegerField(choices=Poids.choices)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    stock_sacs = models.PositiveIntegerField(default=0)
    # Généré automatiquement si vide (voir save())
    code_lot = models.CharField(max_length=50, unique=True, blank=True)
    est_actif = models.BooleanField(default=True)
    statut = models.CharField(
        max_length=20, choices=Statut.choices, default=Statut.EN_LIGNE
    )
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='produits/', blank=True, null=True)
    gererer_qr = models.BooleanField(default=True)
    # Traçabilité : quelle commande paddy a servi à fabriquer ce produit
    stock_source = models.ForeignKey(
        CommandePaddy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produits',
    )
    cree_le = models.DateTimeField(auto_now_add=True)
    mis_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['-cree_le']

    @property
    def photo_url(self):
        """Photo du produit, sinon photo par défaut de son type, sinon ''."""
        if self.photo:
            return self.photo.url
        chemin = PHOTOS_PAR_TYPE.get(self.type_riz)
        return static(chemin) if chemin else ''

    def save(self, *args, **kwargs):
        if not self.code_lot:
            self.code_lot = _generer_code_lot()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} — {self.poids_kg} kg ({self.code_lot})"
