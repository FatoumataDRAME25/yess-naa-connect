from django.contrib import admin
from .models import Client, CommandeClient, LigneCommande


class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 0
    readonly_fields = ('sous_total',)

    def sous_total(self, obj):
        return obj.quantite * obj.prix_unitaire
    sous_total.short_description = 'Sous-total'


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display  = ('prenom', 'nom', 'telephone', 'adresse')
    search_fields = ('prenom', 'nom', 'telephone')


@admin.register(CommandeClient)
class CommandeClientAdmin(admin.ModelAdmin):
    list_display  = ('pk', 'client', 'statut', 'mode_paiement', 'date', 'get_total')
    list_filter   = ('statut', 'mode_paiement')
    search_fields = ('client__prenom', 'client__nom', 'client__telephone')
    list_editable = ('statut',)
    readonly_fields = ('date',)
    inlines = (LigneCommandeInline,)

    def get_total(self, obj):
        total = sum(l.quantite * l.prix_unitaire for l in obj.lignes.all())
        return f"{int(total):,} FCFA".replace(',', ' ')
    get_total.short_description = 'Total'


@admin.register(LigneCommande)
class LigneCommandeAdmin(admin.ModelAdmin):
    list_display = ('commande', 'produit', 'quantite', 'prix_unitaire')
    search_fields = ('commande__pk', 'produit__nom')
