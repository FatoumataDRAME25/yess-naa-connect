# Guide de déploiement — Riz Local

## État du projet

Le projet est bien structuré pour la production. Voici ce qui est déjà en place :

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` lisent depuis `.env` (pas de valeurs hardcodées)
- Les settings HTTPS s'activent automatiquement quand `DEBUG=False`
- Basculement SQLite → PostgreSQL via `.env` déjà prévu
- `.env` est dans le `.gitignore` (ne sera jamais poussé sur Git)
- `STATIC_ROOT` et `MEDIA_ROOT` configurés

---

## Ce qu'il faut faire MAINTENANT (avant d'acheter le VPS)

### 1. Mettre à jour requirements.txt
```bash
pip freeze > requirements.txt
```
Vérifier que le fichier contient bien `gunicorn` et `psycopg2-binary`.
Si non, les installer :
```bash
pip install gunicorn psycopg2-binary
pip freeze > requirements.txt
```

### 2. Compiler le CSS Tailwind pour la production
```bash
python manage.py tailwind build
```
Ce fichier CSS minifié sera servi en prod. Sans cette étape, les styles ne s'affichent pas.

### 3. Tester en mode production en local (optionnel mais recommandé)
Modifier temporairement le `.env` local :
```
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1
```
Lancer :
```bash
python manage.py collectstatic
python manage.py runserver
```
Vérifier que tout s'affiche correctement, puis remettre `DEBUG=True`.

### 4. Pousser le code sur GitHub/GitLab
S'assurer que `.env`, `db.sqlite3` et `media/` ne sont PAS inclus (déjà dans `.gitignore`).

---

## Hébergeur choisi : LWS (lws.fr)

### Ce qu'il faut acheter

- **Un VPS** (et NON un hébergement mutualisé — le mutualisé LWS est fait pour PHP/WordPress, pas pour Django)
- RAM recommandée : **minimum 2 Go** pour être à l'aise avec PostgreSQL + Gunicorn
- OS recommandé : **Ubuntu 22.04 LTS**
- Un **nom de domaine** (LWS propose des `.fr`, `.com`, `.sn` pour un projet sénégalais)

### Après l'achat

1. Pointer le nom de domaine vers l'IP du VPS dans les DNS LWS
   - Délai de propagation DNS : 24 à 48 heures
2. Noter l'adresse IP du VPS fournie par LWS

---

## Ce qu'il faut faire APRÈS l'achat du VPS + domaine

### Sur le VPS (via SSH)

```bash
# Connexion au VPS
ssh root@IP_DU_VPS

# Mise à jour du système
apt update && apt upgrade -y

# Installation des outils
apt install python3-pip python3-venv nginx postgresql postgresql-contrib git -y
```

### Cloner le projet et installer les dépendances
```bash
git clone https://github.com/TON_COMPTE/yess-naa-connect.git /var/www/rizlocal
cd /var/www/rizlocal
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Créer le fichier .env de production
```bash
nano .env
```
Contenu à remplir :
```
DJANGO_SECRET_KEY=une_cle_secrete_longue_et_aleatoire
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tondomaine.com www.tondomaine.com

DB_ENGINE=postgresql
DB_NAME=rizlocal_db
DB_USER=rizlocal_user
DB_PASSWORD=mot_de_passe_fort
DB_HOST=localhost
DB_PORT=5432
```

### Créer la base de données PostgreSQL
```bash
sudo -u postgres psql
CREATE DATABASE rizlocal_db;
CREATE USER rizlocal_user WITH PASSWORD 'mot_de_passe_fort';
GRANT ALL PRIVILEGES ON DATABASE rizlocal_db TO rizlocal_user;
\q
```

### Finaliser le déploiement Django
```bash
python manage.py migrate
python manage.py collectstatic
python manage.py tailwind build
```

### Configurer Gunicorn (serveur d'application)
Créer le fichier service systemd :
```bash
nano /etc/systemd/system/rizlocal.service
```
Contenu :
```ini
[Unit]
Description=Gunicorn pour Riz Local
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/rizlocal
ExecStart=/var/www/rizlocal/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/rizlocal.sock \
    yessnaaconnect.wsgi:application

[Install]
WantedBy=multi-user.target
```
Activer :
```bash
systemctl enable rizlocal
systemctl start rizlocal
```

### Configurer Nginx (serveur web)
```bash
nano /etc/nginx/sites-available/rizlocal
```
Contenu :
```nginx
server {
    listen 80;
    server_name tondomaine.com www.tondomaine.com;

    location /static/ {
        alias /var/www/rizlocal/staticfiles/;
    }

    location /media/ {
        alias /var/www/rizlocal/media/;
    }

    location / {
        proxy_pass http://unix:/run/rizlocal.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Activer :
```bash
ln -s /etc/nginx/sites-available/rizlocal /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Activer le SSL (HTTPS) — gratuit avec Let's Encrypt
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d tondomaine.com -d www.tondomaine.com
```
Le certificat se renouvelle automatiquement.

### Transférer les fichiers médias (photos produits)
Depuis ta machine locale :
```bash
scp -r media/ root@IP_DU_VPS:/var/www/rizlocal/
```

---

## Ce qui n'est pas encore configuré (à anticiper)

- **Emails** : pas de configuration SMTP pour les confirmations de commande. Si besoin plus tard, ajouter les settings EMAIL_* dans `.env`.
- **Sauvegardes automatiques** de la base de données : à configurer avec un cron job sur le VPS.

---

## Résumé rapide

| Étape | Quand | Statut |
|-------|-------|--------|
| `pip freeze > requirements.txt` | Maintenant | À faire |
| `tailwind build` | Maintenant | À faire |
| Pousser sur Git | Maintenant | À faire |
| Acheter VPS + domaine sur LWS | Quand prêt | En attente |
| Pointer DNS vers IP VPS | Après achat | En attente (24-48h) |
| Installer Nginx + Gunicorn | Après achat | En attente |
| Créer `.env` production | Après achat | En attente |
| `migrate` + `collectstatic` | Après achat | En attente |
| Certificat SSL Let's Encrypt | Après achat | En attente |
| Transférer les médias | Après achat | En attente |
