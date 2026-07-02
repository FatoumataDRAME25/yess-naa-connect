from django.db import models


class Produit(models.Model):
    CATEGORIE_CHOICES = [
        ('blanc',   'Riz Blanc'),
        ('parfume', 'Riz Parfumé'),
        ('complet', 'Riz Complet'),
        ('brisure', 'Brisure'),
    ]

    nom            = models.CharField(max_length=200)
    description    = models.TextField(blank=True)
    prix           = models.DecimalField(max_digits=10, decimal_places=0)
    image          = models.ImageField(upload_to='produits/', blank=True, null=True)
    stock          = models.PositiveIntegerField(default=0)
    categorie      = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='blanc')
    poids_options  = models.CharField(max_length=100, default='5kg,10kg,25kg')
    tracable       = models.BooleanField(default=True)
    actif          = models.BooleanField(default=True)

    # Champs page détail
    origine        = models.CharField(max_length=100, default='Mbour, Sénégal')
    producteur_info= models.CharField(
        max_length=255,
        default='Transformé par YEES NAA CONNECT à partir de paddy local.',
        verbose_name='Info producteur'
    )
    # Points forts du produit (un par ligne)
    points_forts   = models.TextField(
        blank=True,
        default='Zéro pesticide chimique de synthèse\nTaux de brisure inférieur à 5%\nRiche en fibres naturelles et minéraux',
        help_text='Un point fort par ligne'
    )
    note           = models.DecimalField(max_digits=3, decimal_places=1, default=4.8)
    nb_avis        = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.nom

    def get_poids_liste(self):
        return [p.strip() for p in self.poids_options.split(',')]

    def get_points_forts_liste(self):
        """Retourne la liste des points forts (une ligne = un point)."""
        return [p.strip() for p in self.points_forts.splitlines() if p.strip()]
