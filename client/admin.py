from django.contrib import admin
from .models import Client, CommandeClient, LigneCommande


# ---------------- CLIENT ----------------
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'prenom', 'nom', 'telephone', 'adresse')
    search_fields = ('prenom', 'nom', 'telephone')
    list_per_page = 20


# ---------------- COMMANDE CLIENT ----------------
class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 1


@admin.register(CommandeClient)
class CommandeClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'statut', 'mode_paiement', 'date')
    list_filter = ('statut', 'mode_paiement', 'date')
    search_fields = ('client__prenom', 'client__nom', 'client__telephone')
    inlines = [LigneCommandeInline]
    list_per_page = 20


# ---------------- LIGNE COMMANDE ----------------
@admin.register(LigneCommande)
class LigneCommandeAdmin(admin.ModelAdmin):
    list_display = ('id', 'commande', 'produit', 'quantite', 'prix_unitaire')
    list_filter = ('produit',)
    search_fields = ('commande__id', 'produit__nom')