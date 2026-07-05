from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Pages
    path("", views.accueil, name="accueil"),
    path("a-propos/", views.a_propos, name="a_propos"),
    path("cat/", views.catalogue, name="catalogue"),
    path('produit/<int:produit_id>/', views.produit_detail, name='produit_detail'),
    path("panier/", views.panier, name="panier"),
    path("commande/", views.finaliser_commande, name="finaliser_commande"),
    path("confirmationCommande/", views.confirmer_commande, name="confirmationCommande"),
    path("suivreCommande/", views.suivre_commande, name="suivre_commande"),
    path("commande/<str:numero>/recu/", views.recu_commande, name="recu_commande"),
    path("commande/<str:numero>/recu/pdf/", views.recu_commande_pdf, name="recu_commande_pdf"),
    path("verification/", views.verification_qrcode, name="verification_qrcode"),

    # Actions panier (AJAX POST)
    path("panier/ajouter/<int:produit_id>/", views.ajouter_au_panier, name="ajouter_au_panier"),
    path("panier/modifier/<int:produit_id>/", views.modifier_quantite, name="modifier_quantite"),
    path("panier/supprimer/<int:produit_id>/", views.supprimer_du_panier, name="supprimer_du_panier"),
    path("panier/vider/", views.vider_panier, name="vider_panier"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
