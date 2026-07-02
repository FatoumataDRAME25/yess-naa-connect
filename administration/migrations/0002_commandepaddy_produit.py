# Migration manuelle — déplace CommandePaddy et Produit de l'app producteur
# vers l'app transformatrice_admin (administration).

import django.db.models.deletion
import administration.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transformatrice_admin', '0001_initial'),
        ('producteur', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommandePaddy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantite_commande', models.DecimalField(decimal_places=2, max_digits=10)),
                ('date_livraison', models.DateField(blank=True, null=True)),
                ('note', models.CharField(blank=True, max_length=255)),
                ('statut', models.CharField(
                    choices=[
                        ('en_attente', 'En attente'),
                        ('confirmee', 'Confirmée'),
                        ('recue', 'Reçue'),
                        ('annulee', 'Annulée'),
                    ],
                    default='en_attente',
                    max_length=20,
                )),
                ('cree_le', models.DateTimeField(auto_now_add=True)),
                ('commande_par', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='commandes_paddy_passees',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('stock', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='commandes_paddy',
                    to='producteur.stockpaddy',
                )),
            ],
            options={
                'verbose_name': 'Commande paddy',
                'verbose_name_plural': 'Commandes paddy',
                'ordering': ['-cree_le'],
            },
        ),
        migrations.CreateModel(
            name='Produit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=150)),
                ('type_riz', models.CharField(
                    choices=[('blanc', 'Blanc'), ('etuve', 'Étuvé'), ('parfume', 'Parfumé')],
                    max_length=20,
                )),
                ('poids_kg', models.PositiveSmallIntegerField(
                    choices=[(5, '5 kg'), (10, '10 kg'), (25, '25 kg')],
                )),
                ('prix', models.DecimalField(decimal_places=2, max_digits=10)),
                ('stock_sacs', models.PositiveIntegerField(default=0)),
                ('code_lot', models.CharField(blank=True, max_length=50, unique=True)),
                ('est_actif', models.BooleanField(default=True)),
                ('statut', models.CharField(
                    choices=[
                        ('en_ligne', 'En ligne'),
                        ('rupture', 'Rupture de stock'),
                        ('archive', 'Archivé'),
                    ],
                    default='en_ligne',
                    max_length=20,
                )),
                ('description', models.TextField(blank=True)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='produits/')),
                ('gererer_qr', models.BooleanField(default=True)),
                ('cree_le', models.DateTimeField(auto_now_add=True)),
                ('mis_a_jour', models.DateTimeField(auto_now=True)),
                ('stock_source', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='produits',
                    to='transformatrice_admin.commandepaddy',
                )),
            ],
            options={
                'verbose_name': 'Produit',
                'verbose_name_plural': 'Produits',
                'ordering': ['-cree_le'],
            },
        ),
    ]
