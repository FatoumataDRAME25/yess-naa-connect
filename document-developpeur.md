# Document de passation — Développeur Yeesnaa Connect
## Tout ce qu'il faut savoir pour reprendre, maintenir et faire évoluer la plateforme

---

## 1. Informations du projet

| Élément | Valeur |
|---------|--------|
| Nom du projet | Yess Naa Connect |
| Site en production | https://yeesnaa.com |
| Dépôt GitHub | https://github.com/FatoumataDRAME25/yess-naa-connect |
| Branche principale | `master` |
| VPS | LWS — IP `180.149.197.231` |
| OS serveur | Ubuntu 24.04 LTS |
| Répertoire production | `/var/www/rizlocal` |

---

## 2. Stack technique

| Couche | Technologie | Version |
|--------|-------------|---------|
| Backend | Django | 6.0.6 |
| Base de données (prod) | PostgreSQL | via psycopg2-binary 2.9.12 |
| Base de données (dev) | SQLite | — |
| CSS | Tailwind CSS + DaisyUI | via django-tailwind 4.5.0 |
| Serveur d'application | Gunicorn | 26.0.0 |
| Serveur web | Nginx | — |
| SSL | Let's Encrypt (Certbot) | auto-renouvelé |
| QR codes | qrcode | 8.2 |
| PDF | WeasyPrint | 69.0 |
| Variables d'env | python-dotenv | 1.2.2 |

---

## 3. Accès nécessaires à récupérer

> ⚠️ Ces accès ne sont PAS dans ce document pour des raisons de sécurité.
> La personne qui te transmet ce document doit te fournir séparément :

### 3.1 GitHub
- **Accès au dépôt** : être ajouté comme collaborateur sur `https://github.com/FatoumataDRAME25/yess-naa-connect`
- **Token GitHub** : le token actuel expire dans ~2 mois. Créer un nouveau Personal Access Token (PAT) sur https://github.com/settings/tokens avec les droits `repo` + `workflow`
- Mettre à jour les credentials Git sur le serveur :
```bash
ssh root@180.149.197.231
cd /var/www/rizlocal
git remote set-url origin https://TON_TOKEN@github.com/FatoumataDRAME25/yess-naa-connect.git
```

### 3.2 VPS LWS
- **Accès SSH** : `ssh root@180.149.197.231` (mot de passe fourni par LWS)
- **Panel LWS** : https://panel.lws.fr — identifiants compte LWS de la cliente
- Renouvellement VPS et domaine géré depuis ce panel

### 3.3 Fichier `.env` de production
Se trouve sur le serveur à `/var/www/rizlocal/.env`. **Ne jamais committer ce fichier.**
Contient : `DJANGO_SECRET_KEY`, `DB_PASSWORD`, `DJANGO_ALLOWED_HOSTS`, etc.
Demander le contenu à la personne qui te transmet ce projet.

### 3.4 Base de données PostgreSQL (production)
```
DB_NAME     = yessnaaconnect
DB_USER     = yessnaaconnect_user
DB_HOST     = localhost
DB_PORT     = 5432
DB_PASSWORD = [à récupérer depuis /var/www/rizlocal/.env]
```

---

## 4. Mise en place en local (première fois)

```bash
# 1. Cloner le dépôt
git clone https://github.com/FatoumataDRAME25/yess-naa-connect.git
cd yess-naa-connect

# 2. Environnement virtuel Python
python3 -m venv venv
source venv/bin/activate      # Linux/Mac
# ou : venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Créer le fichier .env local
cp .env.example .env
# Editer .env : laisser DEBUG=True, SQLite par défaut, mettre une SECRET_KEY

# 5. Appliquer les migrations
python manage.py migrate

# 6. Créer un compte admin local
python manage.py shell
>>> from administration.models import User
>>> u = User.objects.create_superuser('admin', password='admin123', prenom='Admin', nom='Local', telephone='0000000000', role='admin')
>>> exit()

# 7. Installer et démarrer Tailwind (terminal séparé)
python manage.py tailwind install
python manage.py tailwind start

# 8. Lancer le serveur
python manage.py runserver
```

Accéder à :
- Boutique : http://localhost:8000
- Espace admin : http://localhost:8000/espace-admin/connexion/
- Django admin natif : http://localhost:8000/admin/

---

## 5. Structure du projet

```
yess-naa-connect/
├── yessnaaconnect/          # Config principale (settings.py, urls.py, wsgi.py)
├── administration/          # App transformatrice/admin
│   ├── models.py            # User, Produit, CommandePaddy, RegleRemise
│   ├── views.py             # Toutes les vues de l'espace admin
│   ├── urls.py              # namespace: admin_transformatrice
│   └── templates/espace_admin/
├── client/                  # Vitrine publique (sans compte)
│   ├── models.py            # Client, CommandeClient, LigneCommande
│   ├── views.py             # Panier, commande, suivi, pages légales
│   ├── urls.py
│   └── templates/client/
├── livreur/                 # Espace livreurs
│   ├── models.py            # Livreur, Livraison
│   ├── views.py
│   └── templates/livreur/
├── producteur/              # Espace producteurs
│   ├── models.py            # Producteur, StockPaddy
│   ├── views.py
│   └── templates/          # (templates à plat, pas dans sous-dossier)
├── theme/                   # Configuration Tailwind CSS
│   └── static_src/src/styles.css   # ← Ajouter les custom CSS ici
├── static/                  # Fichiers statiques globaux
├── media/                   # Uploads (photos produits, stocks, avatars)
├── templates/               # Templates globaux (404.html)
├── requirements.txt
├── .env.example             # Modèle de configuration
└── deploy.sh                # Script de déploiement rapide
```

---

## 6. Workflow de déploiement

### Modifier du code et déployer en production

```bash
# 1. Modifier le code en local
# 2. Vérifier qu'il n'y a pas d'erreurs
python manage.py check

# 3. Si modification de modèles → créer les migrations
python manage.py makemigrations
python manage.py migrate  # en local pour vérifier

# 4. Committer et pousser sur GitHub
git add .
git commit -m "description courte des changements"
git push origin master

# 5. Se connecter au VPS et déployer
ssh root@180.149.197.231
cd /var/www/rizlocal && ./deploy.sh
```

### Ce que fait `deploy.sh` automatiquement
1. `git pull origin master` — récupère le code
2. `pip install -r requirements.txt` — met à jour les dépendances
3. `python manage.py tailwind build` — recompile le CSS Tailwind
4. `python manage.py collectstatic` — copie les fichiers statiques
5. `python manage.py migrate` — applique les nouvelles migrations
6. `chown -R www-data` — corrige les permissions
7. `systemctl restart rizlocal` — redémarre Gunicorn

### Commandes utiles sur le serveur

```bash
# Voir les logs en temps réel
journalctl -u rizlocal -f

# Redémarrer si le site ne répond plus
systemctl restart rizlocal
systemctl restart nginx

# Vérifier l'état des services
systemctl status rizlocal
systemctl status nginx

# Accéder au shell Django en production
cd /var/www/rizlocal && source venv/bin/activate
python manage.py shell

# Voir les erreurs Nginx
tail -f /var/log/nginx/error.log
```

---

## 7. Points importants à connaître

### Tailwind CSS en production
- Les classes CSS sont **purgées** en production (seules les classes utilisées dans les templates sont conservées)
- **Ne jamais** utiliser des classes dynamiques construites en JS avec `classList.add('nom-classe')` si la classe n'apparaît nulle part dans le HTML — elles seront purgées
- Toujours utiliser `style="display:flex"` plutôt que `classList.add('flex')` pour les éléments affichés/cachés dynamiquement
- Après toute modification de template : reconstruire le CSS avec `python manage.py tailwind build`

### Modèle utilisateur personnalisé
- Le username Django = numéro de téléphone
- Connexion toujours par téléphone, jamais par email
- `AUTH_USER_MODEL = 'administration.User'` — ne jamais changer après les premières migrations

### Cookies et Tailwind
- Le bandeau cookies utilise `style="display:none"` (pas `hidden`) pour contourner la purge Tailwind
- Le consentement est stocké dans `localStorage` (clé : `yn_cookies_accepted`)

### Remise volume
- Configurée via l'espace admin → "Remise volume" (`/espace-admin/remise/`)
- Stockée dans le modèle `RegleRemise` (seuil en kg, taux en %)
- La règle actuelle : **3 000 kg → 5%**
- La remise est calculée côté serveur dans `client/views.py` → `calculer_remise()`

### Dashboard livreur
- Affiche toutes les livraisons **non confirmées** assignées au livreur (pas seulement celles du jour)
- + les livraisons confirmées aujourd'hui
- Fichier : `livreur/views.py` → fonction `dashboard()`

---

## 8. Fonctionnalités en attente (à implémenter)

| Fonctionnalité | Priorité | Notes |
|----------------|----------|-------|
| Paiement Mobile Money (Orange Money / Wave) | Haute | Voir `mobile-money.md` — attendre clés API PayDunya de la cliente |
| Notifications SMS à la commande | Moyenne | Intégrer Twilio ou un opérateur local |
| Tableau de bord statistiques avancé | Basse | Évolution du CA, top produits, etc. |

---

## 9. Architecture en production

```
Internet
   │
   ▼
Nginx (port 80/443)
   │  ← Sert static/ et media/ directement
   │  ← Proxy les autres requêtes vers Gunicorn
   ▼
Gunicorn (socket Unix : /run/rizlocal/rizlocal.sock)
   │
   ▼
Django (yessnaaconnect.wsgi:application)
   │
   ▼
PostgreSQL (localhost:5432)
```

Fichiers de config serveur :
- Nginx : `/etc/nginx/sites-available/rizlocal`
- Gunicorn service : `/etc/systemd/system/rizlocal.service`
- Renouvellement SSL : automatique via Certbot (cron)

---

## 10. Renouvellement du token GitHub

Le token GitHub actuel expire bientôt. Pour le renouveler :

1. Aller sur https://github.com/settings/tokens
2. Cliquer "Generate new token (classic)"
3. Cocher `repo` (accès complet aux dépôts privés)
4. Copier le token généré
5. Sur le VPS, mettre à jour l'URL du remote :

```bash
ssh root@180.149.197.231
cd /var/www/rizlocal
git remote set-url origin https://NOUVEAU_TOKEN@github.com/FatoumataDRAME25/yess-naa-connect.git
# Vérifier que ça marche :
git fetch origin
```

6. En local sur ta machine également :
```bash
git remote set-url origin https://NOUVEAU_TOKEN@github.com/FatoumataDRAME25/yess-naa-connect.git
```

---

## 11. Contacts et ressources

| Ressource | Lien |
|-----------|------|
| Dépôt GitHub | https://github.com/FatoumataDRAME25/yess-naa-connect |
| Panel LWS | https://panel.lws.fr |
| Documentation Django 6 | https://docs.djangoproject.com/en/6.0/ |
| Documentation Tailwind | https://tailwindcss.com/docs |
| PayDunya (paiement futur) | https://paydunya.com/developers |
| Documentation technique complète | `documentation.md` (dans le projet) |
| Guide de déploiement initial | `DEPLOIEMENT_COMPLET.md` (dans le projet) |
| Fonctionnalités implémentées en dernier| `retour.md` (dans le projet) |
| Intégration Mobile Money | `mobile-money.md` (dans le projet) |

---

*Document rédigé le 3 septembre 2026 — Projet Yeesnaa Connect*
