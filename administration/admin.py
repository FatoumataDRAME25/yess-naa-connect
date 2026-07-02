from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, CommandePaddy, Produit


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'prenom', 'nom', 'telephone', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'prenom', 'nom', 'telephone')
    ordering = ('-date_joined',)
    list_editable = ('role', 'is_active')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profil métier', {
            'fields': ('role', 'prenom', 'nom', 'telephone', 'photo', 'adresse')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Profil métier', {
            'fields': ('role', 'prenom', 'nom', 'telephone', 'adresse')
        }),
    )


@admin.register(CommandePaddy)
class CommandePaddyAdmin(admin.ModelAdmin):
    list_display = ('pk', 'stock', 'commande_par', 'quantite_commande', 'date_livraison', 'statut', 'cree_le')
    list_filter = ('statut',)
    search_fields = ('commande_par__username', 'stock__producteur__user__nom')
    list_editable = ('statut',)
    readonly_fields = ('cree_le',)
    date_hierarchy = 'cree_le'


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type_riz', 'poids_kg', 'prix', 'stock_sacs', 'est_actif', 'code_lot', 'stock_source', 'cree_le')
    list_filter = ('type_riz', 'poids_kg', 'est_actif', 'statut')
    search_fields = ('nom', 'code_lot')
    list_editable = ('est_actif', 'stock_sacs')
    readonly_fields = ('code_lot', 'cree_le', 'mis_a_jour')
    raw_id_fields = ('stock_source',)
    date_hierarchy = 'cree_le'
