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
    photo = models.ImageField(upload_to='stocks_paddy/')
    description = models.TextField(blank=True, default='')
    date_recolte = models.DateField()
    region = models.CharField(max_length=100)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.DISPONIBLE)
    est_bio = models.BooleanField(default=False)

    def __str__(self):
        return f"Stock #{self.pk} - {self.get_variete_display()} ({self.quantite_kg} kg)"
