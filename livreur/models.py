from django.conf import settings
from django.db import models


class Livreur(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='livreur_profile'
    )

    def __str__(self):
        return f"Livreur: {self.user.prenom} {self.user.nom}"


class Livraison(models.Model):
    commande = models.OneToOneField(
        'client.CommandeClient', on_delete=models.CASCADE, related_name='livraison'
    )
    livreur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='livraisons'
    )
    montant_encaisse = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    confirme_le = models.DateTimeField(null=True, blank=True)

    def confirmer(self, montant=None):
        """Confirme la livraison et met à jour le statut de la commande liée."""
        from django.utils import timezone
        self.confirme_le = timezone.now()
        if montant is not None:
            self.montant_encaisse = montant
        self.save()
        self.commande.statut = self.commande.Statut.LIVREE
        self.commande.save(update_fields=['statut'])

    def __str__(self):
        return f"Livraison #{self.pk} - Commande #{self.commande_id}"
