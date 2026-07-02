from django.contrib import admin

from .models import Producteur, StockPaddy


@admin.register(Producteur)
class ProducteurAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_telephone', 'get_adresse')
    search_fields = ('user__prenom', 'user__nom', 'user__telephone')

    def get_telephone(self, obj):
        return obj.user.telephone
    get_telephone.short_description = 'Téléphone'

    def get_adresse(self, obj):
        return obj.user.adresse
    get_adresse.short_description = 'Adresse'


@admin.register(StockPaddy)
class StockPaddyAdmin(admin.ModelAdmin):
    list_display = ('producteur', 'variete', 'quantite_kg', 'prix_par_kg', 'region', 'statut', 'est_bio', 'date_recolte')
    list_filter = ('variete', 'statut', 'est_bio')
    search_fields = ('producteur__user__prenom', 'producteur__user__nom', 'region')
    list_editable = ('statut',)
