from django.contrib import admin
from .models import Produit


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display  = ('nom', 'categorie', 'prix', 'stock', 'tracable', 'actif')
    list_filter   = ('actif', 'tracable', 'categorie')
    search_fields = ('nom',)
    list_editable = ('prix', 'stock', 'actif')
    fieldsets = (
        ('Informations principales', {
            'fields': ('nom', 'categorie', 'prix', 'image', 'stock', 'poids_options', 'tracable', 'actif')
        }),
        ('Page détail', {
            'fields': ('description', 'origine', 'producteur_info', 'points_forts', 'note', 'nb_avis')
        }),
    )
