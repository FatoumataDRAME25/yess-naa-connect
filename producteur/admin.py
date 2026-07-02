from django.contrib import admin

from django.contrib import admin
from .models import Producteur, StockPaddy, CommandePaddy, Produit


@admin.register(Producteur)
class ProducteurAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    search_fields = ('user__username', 'user__email')


@admin.register(StockPaddy)
class StockPaddyAdmin(admin.ModelAdmin):
    list_display = ('id', 'producteur', 'variete', 'quantite_kg', 'prix_par_kg', 'statut', 'est_bio')
    list_filter = ('variete', 'statut', 'est_bio', 'region')
    search_fields = ('producteur__user__username', 'region')


@admin.register(CommandePaddy)
class CommandePaddyAdmin(admin.ModelAdmin):
    list_display = ('id', 'stock', 'commande_par', 'quantite_commande', 'statut', 'cree_le')
    list_filter = ('statut', 'cree_le')
    search_fields = ('stock__id', 'commande_par__username')


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'type_riz', 'poids_kg', 'prix', 'stock_sacs', 'est_actif')
    list_filter = ('type_riz', 'poids_kg', 'est_actif')
    search_fields = ('nom', 'code_lot')