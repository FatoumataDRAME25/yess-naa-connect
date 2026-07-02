from django.contrib import admin
from .models import Livreur, Livraison


@admin.register(Livreur)
class LivreurAdmin(admin.ModelAdmin):
    list_display  = ('user', 'get_telephone')
    search_fields = ('user__prenom', 'user__nom', 'user__telephone')

    def get_telephone(self, obj):
        return obj.user.telephone
    get_telephone.short_description = 'Téléphone'


@admin.register(Livraison)
class LivraisonAdmin(admin.ModelAdmin):
    list_display  = ('pk', 'commande', 'livreur', 'montant_encaisse', 'confirme_le')
    list_filter   = ('confirme_le',)
    search_fields = ('commande__pk', 'livreur__prenom', 'livreur__nom')
    readonly_fields = ('confirme_le',)
