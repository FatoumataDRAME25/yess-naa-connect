# Documentation — Yess Naa Connect

## Vue d'ensemble

**Yess Naa Connect** est une plateforme de vente de riz local au Sénégal. Elle connecte les producteurs de paddy, la transformatrice (administratrice), les livreurs et les clients finaux. La chaîne de valeur complète — de la récolte jusqu'à la livraison — est tracée via des QR codes.

---

## Architecture du projet

```
yess-naa-connect/
├── yessnaaconnect/       # Configuration principale (settings, urls racine, wsgi)
├── administration/       # App admin/transformatrice
├── client/               # Vitrine publique (sans compte)
├── livreur/              # Espace livreurs
├── producteur/           # Espace producteurs
├── theme/                # Thème Tailwind (django-tailwind)
├── static/               # Fichiers statiques globaux (JS, fonts, images)
├── media/                # Uploads (photos produits, stocks, avatars)
├── db.sqlite3            # Base SQLite (dev)
├── requirements.txt
└── .env
```

---

## Stack technique

| Élément | Détail |
|---|---|
| Framework | Django 6.0.6 |
| Base de données | SQLite (dev) / PostgreSQL (prod via `DB_ENGINE=postgresql`) |
| CSS | Tailwind CSS + DaisyUI via django-tailwind |
| Charts | Chart.js (dashboard admin) |
| Images | Pillow 12.2.0 |
| QR codes | qrcode 8.2 |
| Variables d'env | python-dotenv 1.2.2 |
| PostgreSQL | psycopg2-binary 2.9.12 |

**Langue** : `fr-fr` — **Fuseau horaire** : `Africa/Dakar`

---

## Configuration (`settings.py`)

- Modèle utilisateur personnalisé : `AUTH_USER_MODEL = 'administration.User'`
- Secrets lus depuis `.env` : `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DB_*`
- En production (`DEBUG=False`) : HTTPS forcé, HSTS 1 an, cookies sécurisés, proxy SSL header
- Fichiers statiques : `/static/` → `static/`, collectés dans `staticfiles/`
- Fichiers media : `/media/` → `media/`

---

## Modèles de données

### App `administration`

#### `User` (étend `AbstractUser`)
| Champ | Type | Description |
|---|---|---|
| `prenom`, `nom` | CharField | Identité |
| `telephone` | CharField | Sert de `username` pour la connexion |
| `role` | CharField | `producteur` / `livreur` / `admin` |
| `photo` | ImageField | Avatar |
| `adresse` | CharField | Région pour les producteurs |

Manager custom : `create_producteur()`, `create_livreur()`, `create_admin_role()`

#### `Produit` — Riz fini en vente
| Champ | Type | Description |
|---|---|---|
| `nom`, `description` | Texte | Libellé |
| `type_riz` | choices | `blanc / etuve / parfume` |
| `poids_kg` | choices | `5 / 10 / 25 kg` |
| `prix` | Decimal | Prix de vente |
| `stock_sacs` | Integer | Quantité en stock |
| `code_lot` | CharField unique | Auto-généré `RIZ-<8hex>` |
| `statut` | choices | `en_ligne / rupture / archive` |
| `stock_source` | FK → `CommandePaddy` | Lien de traçabilité (nullable) |
| `photo` | ImageField | `produits/` |

#### `CommandePaddy` — Commande interne de paddy (admin → producteur)
| Champ | Type | Description |
|---|---|---|
| `stock` | FK → `StockPaddy` | Lot commandé |
| `commande_par` | FK → `User` | Admin qui commande |
| `quantite_commande` | Decimal | En kg |
| `statut` | choices | `en_attente / confirmee / recue / annulee` |
| `date_livraison`, `note` | Divers | Optionnels |

---

### App `client`

#### `Client` — Acheteur anonyme (pas de compte)
`prenom`, `nom`, `telephone`, `adresse`

#### `CommandeClient` — Commande d'un client
| Champ | Type | Description |
|---|---|---|
| `numero` | CharField unique | Auto-généré `YEES-<année>-<4 chars>` |
| `client` | FK → `Client` | |
| `statut` | choices | `attente / preparation / en_livraison / livree / annulee` |
| `mode_paiement` | CharField | Ex : `livraison`, `mobile_money` |
| `adresse_livraison` | CharField | Texte |
| `latitude`, `longitude` | Float | GPS client (nullable) |
| `frais_livraison` | Integer | FCFA |

Propriétés calculées : `sous_total`, `total`, `montant`, `maps_url`, `produits_resume`

#### `LigneCommande` — Articles de la commande
`commande` → `CommandeClient`, `produit` → `Produit`, `quantite`, `prix_unitaire`

---

### App `livreur`

#### `Livreur` — Profil (1-to-1 avec `User`)

#### `Livraison` — Assignation d'une livraison
| Champ | Type | Description |
|---|---|---|
| `commande` | OneToOne → `CommandeClient` | |
| `livreur` | FK → `User` | |
| `montant_encaisse` | Decimal | Collecté à la livraison |
| `confirme_le` | DateTimeField | Null jusqu'à confirmation |

Méthode `confirmer(montant)` : marque la livraison faite et passe la commande en `livree`.

---

### App `producteur`

#### `Producteur` — Profil (1-to-1 avec `User`)

#### `StockPaddy` — Déclaration de récolte
| Champ | Type | Description |
|---|---|---|
| `producteur` | FK → `Producteur` | |
| `variete` | choices | `blanc / parfume` |
| `quantite_kg`, `prix_par_kg` | Decimal | |
| `region` | CharField | Région sénégalaise |
| `date_recolte` | DateField | |
| `statut` | choices | `disponible / commande / epuise` |
| `est_bio` | Boolean | |
| `photo` | ImageField | `stocks_paddy/` |

---

## URLs et routes

### Racine (`/`)
```
/              → client (vitrine publique)
/espace-admin/ → administration (namespace: admin_transformatrice)
/producteur/   → producteur
/livreur/      → livreur
/admin/        → Django admin natif
```

### Vitrine client (`client/urls.py`) — aucune authentification requise
| URL | Vue | Rôle |
|---|---|---|
| `/` | `landing` | **Page d'ouverture** — portail de sélection des rôles |
| `/accueil/` | `accueil` | Boutique (produits en vedette) |
| `/a-propos/` | `a_propos` | Page institutionnelle |
| `/cat/` | `catalogue` | Catalogue filtrable + pagination AJAX |
| `/produit/<id>/` | `produit_detail` | Détail + QR traçabilité |
| `/panier/` | `panier` | Panier (session) |
| `/confirmationCommande/` | `confirmer_commande` | Formulaire de commande |
| `/commande/` | `finaliser_commande` | Traitement POST commande |
| `/suivreCommande/` | `suivre_commande` | Suivi par n° + téléphone |
| `/commande/<num>/recu/` | `recu_commande` | Reçu imprimable |
| `/verification/` | `verification_qrcode` | Vérification code lot |
| `/panier/ajouter/<id>/` | AJAX POST | Ajouter au panier |
| `/panier/modifier/<id>/` | AJAX POST | +/- quantité |
| `/panier/supprimer/<id>/` | AJAX POST | Retirer article |
| `/panier/vider/` | AJAX POST | Vider panier |

### Espace admin (`/espace-admin/`)
| URL | Rôle |
|---|---|
| `connexion/` | Login admin |
| `dashboard/` | Tableau de bord (stats du jour) |
| `stocks/` | Stocks producteurs + commande paddy |
| `stocks/commandes-paddy/` | Suivi commandes paddy |
| `catalogue/` | Gestion produits |
| `catalogue/ajouter/` | Créer un produit (avec variantes poids) |
| `catalogue/<pk>/modifier/` | Modifier un produit |
| `catalogue/<lot_code>/qr/` | Télécharger QR PNG |
| `commandes/` | Commandes clients (filtres + pagination) |
| `commandes/<pk>/` | Détail + changement statut + assignation livreur |
| `livreurs/` | Création et liste des livreurs |
| `tracabilite/<lot_code>/` | **Page publique** de traçabilité (scannée via QR) |

### Espace producteur (`/producteur/`)
| URL | Rôle |
|---|---|
| `/` | Inscription (auto-registration) |
| `connexion/` | Login |
| `dashbord/` | Dashboard (stocks, commandes) |
| `declaration/` | Déclarer un stock de paddy |
| `mes-recoltes/` | Historique des récoltes |
| `commandes/` | Commandes reçues de l'admin |
| `commandes/<pk>/accepter/` | Accepter → statut `confirmee` |
| `commandes/<pk>/refuser/` | Refuser → statut `annulee`, stock redevient `disponible` |
| `profil/` | Modifier profil |

### Espace livreur (`/livreur/`)
| URL | Rôle |
|---|---|
| `connexion/` | Login |
| `/` | Dashboard — livraisons du jour |
| `livraison/<pk>/` | Détail livraison + QR suivi |
| `livraison/<pk>/confirmer/` | Confirmer livraison |
| `livraison/<pk>/confirmation/` | Page de confirmation |
| `profil/` | Profil livreur |

---

## Flux métier complet

```
[Producteur]
  → Déclare un StockPaddy (variété, quantité, prix, région)

[Admin/Transformatrice]
  → Consulte les stocks disponibles
  → Crée une CommandePaddy (quantité, date livraison, note)
  → Le stock passe en "commandé"

[Producteur]
  → Accepte ou refuse la commande paddy
  → Si acceptée : statut → "confirmée"

[Admin]
  → Marque la commande paddy comme "reçue"
  → Le stock producteur est décrémenté / épuisé
  → Crée un ou plusieurs Produits liés à cette commandePaddy
  → Chaque produit reçoit un code_lot unique + QR code de traçabilité

[Client]
  → Navigue le catalogue, filtre par type/poids
  → Ajoute au panier (session)
  → Saisit nom/téléphone/adresse + GPS optionnel
  → Passe commande → CommandeClient + LigneCommandes créées
  → Reçoit un numéro YEES-xxxx-xxxx

[Admin]
  → Voit la commande arriver
  → Assigne un livreur → Livraison créée, commande passe en "en_livraison"

[Livreur]
  → Voit ses livraisons du jour
  → Peut consulter l'adresse + lien Google Maps
  → Confirme la livraison → montant encaissé enregistré, statut → "livrée"

[Client]
  → Peut suivre sa commande via /suivreCommande/ (n° + téléphone)
  → Peut scanner le QR sur l'emballage → page de traçabilité publique
    (nom du producteur, région, variété, date récolte)
```

---

## Authentification

Tous les portails utilisent le **numéro de téléphone comme identifiant**.

| Portail | Inscription | Accès |
|---|---|---|
| Producteur | Auto-inscription (`/producteur/`) | `role == 'producteur'` |
| Livreur | Créé par l'admin uniquement | `role == 'livreur'` + `LivreurRequiredMixin` |
| Admin | Superuser ou `role == 'admin'` | `@admin_required` |
| Client | Aucun compte — anonyme | — |

---

## Panier et commande client

- Le panier est stocké **en session Django** (aucune écriture en BDD avant validation).
- Structure session : `{ "produit_id": { nom, prix, quantite, image, poids } }`
- À la validation : création de `Client` + `CommandeClient` + `LigneCommande` en une transaction.
- Le numéro de commande (`YEES-<année>-<4chars>`) est garanti unique par boucle de retry.
- Les frais de livraison ne sont pas calculés à la commande (déterminés par le livreur sur place).

---

## Traçabilité QR

1. Chaque `Produit` a un `code_lot` unique (`RIZ-<8hex>`).
2. L'admin peut télécharger le QR PNG (`/espace-admin/catalogue/<lot_code>/qr/`).
3. Ce QR encode l'URL publique `/espace-admin/tracabilite/<lot_code>/`.
4. La page de traçabilité affiche : producteur, région, variété paddy, date récolte, admin qui a commandé.
5. Le client peut aussi saisir le code manuellement sur `/verification/`.

---

## Templates

```
administration/templates/espace_admin/
  base.html                 ← Navbar + layout admin
  dashboard.html            ← Stats du jour, graphiques
  catalogue.html / catalogue_edit.html
  commandes.html / commande_detail.html / commandes_paddy.html
  stocks_producteurs.html
  livreurs.html
  tracabilite.html / tracabilite_introuvable.html
  login.html

client/templates/client/
  base.html                 ← Navbar publique + panier
  accueil.html / a_propos.html
  catalogue.html            ← Filtres + infinite scroll AJAX
  detailProduit.html        ← QR code inline (base64)
  panier.html / finalisercommande.html
  confirmation_commande.html / recu_commande.html
  suivre_commande.html / verification_qrcode.html
  partials/cards_produits.html  ← Partial AJAX pour le catalogue

livreur/templates/livreur/
  connexion.html
  dashboard.html / dashboard_empty.html
  detail_livraison.html / confirmation.html / profil.html

producteur/templates/  (à plat)
  inscription.html / connexion.html
  dashboard_producteur.html / sidebar.html
  declaration_paddy.html / mes_recoltes.html
  comandes.html / profil.html / changer_mot_de_passe.html
```

---

## Variables d'environnement (`.env.example`)

| Variable | Défaut | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | clé insecure | Clé secrète Django |
| `DJANGO_DEBUG` | `True` | Mode debug |
| `DJANGO_ALLOWED_HOSTS` | `localhost 127.0.0.1` | Hôtes autorisés (espace-séparé) |
| `DB_ENGINE` | — | `postgresql` pour activer Postgres |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | — | Credentials PostgreSQL |
| `DB_HOST` | `localhost` | Host PostgreSQL |
| `DB_PORT` | `5432` | Port PostgreSQL |

---

## Démarrage local

```bash
# 1. Environnement virtuel
python -m venv venv
source venv/bin/activate

# 2. Dépendances Python
pip install -r requirements.txt

# 3. Variables d'environnement
cp .env.example .env
# Editer .env si nécessaire

# 4. Base de données
python manage.py migrate

# 5. Superuser
python manage.py createsuperuser

# 6. Tailwind (terminal séparé)
python manage.py tailwind install
python manage.py tailwind start

# 7. Serveur de dev
python manage.py runserver
```
