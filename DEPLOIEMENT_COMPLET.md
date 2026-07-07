# Guide de Déploiement Complet — Riz Local (yeesnaa.com)
## De zéro jusqu'au site en production

---

## Informations du projet

| Élément | Valeur |
|---------|--------|
| Site | https://yeesnaa.com |
| IP VPS | 180.149.197.231 |
| VPS | VPS-122136 (LWS) |
| OS | Ubuntu 24.04 LTS |
| Répertoire | /var/www/rizlocal |
| Dépôt GitHub | https://github.com/FatoumataDRAME25/yess-naa-connect |

---

## PARTIE 1 — Préparation locale (sur ta machine)

### Étape 1 : Mettre à jour requirements.txt
```bash
cd /home/binetou-gueye/Documents/yess-naa-connect
source venv/bin/activate
pip install gunicorn psycopg2-binary weasyprint
pip freeze > requirements.txt
```

### Étape 2 : Pousser le code sur GitHub
```bash
git add .
git commit -m "préparation déploiement"
git push origin master
```

---

## PARTIE 2 — Achat et configuration chez LWS

### Étape 3 : Acheter chez LWS
- Acheter un **VPS M** (8 Go RAM, Ubuntu 24.04 LTS + SSH)
- Acheter un **nom de domaine** (ex: yeesnaa.com)

### Étape 4 : Configurer le DNS
Dans le panel LWS → Domaine → Zone DNS :
- Vérifier que l'enregistrement **A** `@` pointe vers l'IP du VPS (ex: `180.149.197.231`)
- Vérifier que le **CNAME** `www` pointe vers `@`
- Attendre 6 à 24h pour la propagation DNS

---

## PARTIE 3 — Installation sur le VPS

### Étape 5 : Se connecter en SSH
```bash
ssh root@180.149.197.231
```
*(Mot de passe reçu par email de LWS)*

### Étape 6 : Mettre à jour le système
```bash
apt update && apt upgrade -y
```

### Étape 7 : Installer les dépendances système
```bash
apt install python3-pip python3-venv nginx postgresql postgresql-contrib git -y
```

### Étape 8 : Installer Node.js (pour Tailwind)
```bash
apt install ca-certificates curl gnupg apt-transport-https -y
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install nodejs -y
node -v
npm -v
```

### Étape 9 : Créer la base de données PostgreSQL
```bash
sudo -u postgres psql
```
Dans le shell PostgreSQL :
```sql
CREATE DATABASE yessnaaconnect;
CREATE USER yessnaaconnect_user WITH PASSWORD 'VotreMotDePasse';
GRANT ALL PRIVILEGES ON DATABASE yessnaaconnect TO yessnaaconnect_user;
\q
```

### Étape 10 : Cloner le projet
```bash
mkdir -p /var/www/rizlocal
cd /var/www/rizlocal
git clone https://github.com/FatoumataDRAME25/yess-naa-connect.git .
```

### Étape 11 : Créer l'environnement virtuel Python
```bash
cd /var/www/rizlocal
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Étape 12 : Créer le fichier .env de production
```bash
nano /var/www/rizlocal/.env
```
Contenu :
```
DJANGO_SECRET_KEY=une_cle_secrete_longue_et_aleatoire
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yeesnaa.com www.yeesnaa.com 180.149.197.231

DB_ENGINE=postgresql
DB_NAME=yessnaaconnect
DB_USER=yessnaaconnect_user
DB_PASSWORD=VotreMotDePasse
DB_HOST=localhost
DB_PORT=5432

PRODUCTION=True
```
Sauvegarde : `Ctrl+X` → `Y` → `Entrée`

### Étape 13 : Installer les dépendances Tailwind et compiler le CSS
```bash
python manage.py tailwind install
python manage.py tailwind build
```

### Étape 14 : Collecter les fichiers statiques
```bash
python manage.py collectstatic --noinput
```

### Étape 15 : Corriger le lien CSS Tailwind (important)
```bash
ln -sf /var/www/rizlocal/staticfiles/css/dist/styles.css /var/www/rizlocal/staticfiles/css/tailwind.css
```

### Étape 16 : Appliquer les migrations
```bash
python manage.py migrate
```

### Étape 17 : Créer le compte administrateur
```bash
python manage.py shell
```
Dans le shell Python :
```python
from administration.models import User
u = User.objects.get(telephone='0000000000')  # compte par défaut
u.set_password('VotreMotDePasse')
u.telephone = '77XXXXXXX'  # votre vrai numéro
u.prenom = 'Prénom'
u.nom = 'NOM'
u.save()
exit()
```

### Étape 18 : Donner les permissions au dossier
```bash
chown -R www-data:www-data /var/www/rizlocal
```

---

## PARTIE 4 — Configuration Gunicorn (serveur d'application)

### Étape 19 : Créer le service Gunicorn
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
RuntimeDirectory=rizlocal
RuntimeDirectoryMode=0755
ExecStart=/var/www/rizlocal/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/rizlocal/rizlocal.sock \
    yessnaaconnect.wsgi:application

[Install]
WantedBy=multi-user.target
```
Sauvegarde : `Ctrl+X` → `Y` → `Entrée`

### Étape 20 : Démarrer et activer Gunicorn
```bash
systemctl daemon-reload
systemctl enable rizlocal
systemctl start rizlocal
systemctl status rizlocal
```
Vérifier que le socket existe :
```bash
ls -la /run/rizlocal/rizlocal.sock
```

---

## PARTIE 5 — Configuration Nginx (serveur web)

### Étape 21 : Créer la config Nginx
```bash
nano /etc/nginx/sites-available/rizlocal
```
Contenu :
```nginx
server {
    listen 80;
    server_name yeesnaa.com www.yeesnaa.com;

    location /static/ {
        alias /var/www/rizlocal/staticfiles/;
    }

    location /media/ {
        alias /var/www/rizlocal/media/;
    }

    location / {
        proxy_pass http://unix:/run/rizlocal/rizlocal.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Sauvegarde : `Ctrl+X` → `Y` → `Entrée`

### Étape 22 : Activer le site et supprimer le site par défaut
```bash
ln -s /etc/nginx/sites-available/rizlocal /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
systemctl enable nginx
```

### Étape 23 : Vérifier que le site répond
```bash
curl -I -H "Host: yeesnaa.com" http://localhost
```
Doit retourner `301 Moved Permanently` → vers HTTPS (Django redirige)

---

## PARTIE 6 — Certificat SSL (HTTPS gratuit)

### Étape 24 : Installer Certbot
```bash
apt install certbot python3-certbot-nginx -y
```

### Étape 25 : Obtenir le certificat SSL
```bash
certbot --nginx -d yeesnaa.com -d www.yeesnaa.com
```
Répondre aux questions :
- Email → ton adresse email
- Accepter les CGU → `Y`
- Partager avec EFF → `N`

### Étape 26 : Vérifier le certificat
```bash
curl -I https://yeesnaa.com
```
Doit retourner `200 OK`

Le renouvellement automatique est déjà configuré par Certbot (tous les 90 jours).

---

## PARTIE 7 — Vérifications finales

### Étape 27 : Vérifier que tout redémarre automatiquement
```bash
systemctl is-enabled rizlocal
systemctl is-enabled nginx
```
Les deux doivent afficher `enabled`.

### Étape 28 : Créer le script de mise à jour
```bash
nano /var/www/rizlocal/deploy.sh
```
Contenu :
```bash
#!/bin/bash
cd /var/www/rizlocal
source venv/bin/activate
git pull origin master
pip install -r requirements.txt
python manage.py tailwind build
python manage.py collectstatic --noinput
ln -sf /var/www/rizlocal/staticfiles/css/dist/styles.css /var/www/rizlocal/staticfiles/css/tailwind.css
python manage.py migrate
chown -R www-data:www-data /var/www/rizlocal
systemctl restart rizlocal
echo "Déploiement terminé."
```
```bash
chmod +x /var/www/rizlocal/deploy.sh
```

---

## PARTIE 8 — Problèmes rencontrés et solutions

### Problème 1 : Nginx affiche la page par défaut Ubuntu
**Cause** : Le site `default` de Nginx intercepte les requêtes  
**Solution** :
```bash
rm /etc/nginx/sites-enabled/default
systemctl restart nginx
```

### Problème 2 : Permission denied sur le socket Gunicorn
**Cause** : Le socket n'est pas dans le bon répertoire  
**Solution** : Ajouter `RuntimeDirectory=rizlocal` dans le fichier service et utiliser `/run/rizlocal/rizlocal.sock`

### Problème 3 : CSS de l'espace admin ne s'affiche pas
**Cause** : `tailwind.css` n'existe pas, le fichier compilé est dans `dist/styles.css`  
**Solution** :
```bash
ln -sf /var/www/rizlocal/staticfiles/css/dist/styles.css /var/www/rizlocal/staticfiles/css/tailwind.css
```

### Problème 4 : Texte invisible dans les champs de formulaire (espace admin)
**Cause** : DaisyUI v5 réinitialise les couleurs de texte des inputs  
**Solution** : Ajouter dans `theme/static_src/src/styles.css` :
```css
input:not([type="checkbox"]):not([type="radio"]):not([type="range"]),
select,
textarea {
  color: #111827 !important;
  background-color: #ffffff !important;
  border-color: #d1d5db !important;
}
```

### Problème 5 : Couleurs custom Tailwind (yn-green-dark, etc.) absentes
**Cause** : Tailwind v4 ne lit plus `tailwind.config.js` automatiquement  
**Solution** : Définir les couleurs dans `styles.css` avec `@theme { ... }`

---

## Comment mettre à jour le site après modification du code

1. Sur ta machine locale, modifier le code
2. Pousser sur GitHub :
```bash
git add .
git commit -m "description des modifications"
git push origin master
```
3. Se connecter au VPS :
```bash
ssh root@180.149.197.231
```
4. Lancer le script de déploiement :
```bash
cd /var/www/rizlocal && ./deploy.sh
```

---

## Accès au site

| URL | Description |
|-----|-------------|
| https://yeesnaa.com | Boutique publique |
| https://yeesnaa.com/espace-admin/ | Espace administrateur |
| https://yeesnaa.com/producteur/ | Espace producteur |
| https://yeesnaa.com/livreur/ | Espace livreur |
