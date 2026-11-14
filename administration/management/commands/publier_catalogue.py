"""
Publie le catalogue de lancement validé par la cliente (novembre 2026).

    python manage.py publier_catalogue --dry-run      # aperçu, n'écrit rien
    python manage.py publier_catalogue                # crée / met à jour les prix
    python manage.py publier_catalogue --stock 40     # + fixe le stock (sacs)

- Sacs de 25 kg (poids indiqué sur les photos produits).
- Idempotente : un produit est retrouvé par son nom ; relancer la commande
  remet le bon prix et le statut en ligne, sans créer de doublon.
- Le stock n'est modifié que si --stock est passé (sinon 0 à la création).
- Aucune photo n'est enregistrée : chaque produit affiche automatiquement la
  photo de son type (static/images/produits/), sauf si une photo est
  téléversée depuis l'espace admin.
- Les anciens produits ne sont PAS touchés : à retirer depuis l'espace admin.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from administration.models import Produit

POIDS_KG = 25

CATALOGUE = [
    # (nom affiché,     type_riz,    prix FCFA)
    ('Riz entier',     'entier',    Decimal('10000')),
    ('Riz brisé',      'brise',     Decimal('10000')),
    ('Riz extra fin',  'extra_fin', Decimal('10000')),
    ('Riz Basmati',    'basmati',   Decimal('16000')),
]


class Command(BaseCommand):
    help = "Publie les 4 produits du catalogue de lancement (sacs de 25 kg) avec leurs prix."

    def add_arguments(self, parser):
        parser.add_argument('--stock', type=int, default=None,
                            help="Nombre de sacs en stock à fixer pour chaque produit.")
        parser.add_argument('--dry-run', action='store_true',
                            help="Affiche ce qui serait fait sans rien enregistrer.")

    def handle(self, *args, stock=None, dry_run=False, **options):
        if stock is not None and stock < 0:
            self.stderr.write("--stock doit être positif.")
            return

        with transaction.atomic():
            for nom, type_riz, prix in CATALOGUE:
                produit = Produit.objects.filter(nom=nom).order_by('-cree_le').first()
                action = 'Mis à jour' if produit else 'Créé'
                if produit is None:
                    produit = Produit(nom=nom, stock_sacs=stock or 0)

                produit.type_riz = type_riz
                produit.poids_kg = POIDS_KG
                produit.prix = prix
                produit.est_actif = True
                produit.statut = Produit.Statut.EN_LIGNE
                if stock is not None:
                    produit.stock_sacs = stock
                produit.save()

                self.stdout.write(
                    f"{action:11s} {nom:15s} {POIDS_KG} kg  {prix:>7,.0f} FCFA  "
                    f"stock {produit.stock_sacs:>4} sacs  lot {produit.code_lot}".replace(',', ' ')
                )

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("--dry-run : rien n'a été enregistré."))
            else:
                self.stdout.write(self.style.SUCCESS("Catalogue de lancement publié."))
