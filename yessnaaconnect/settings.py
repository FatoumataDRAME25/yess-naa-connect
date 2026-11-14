import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

# ── Clé secrète ─────────────────────────────────────────────────────────────
# En production : définir la variable d'env DJANGO_SECRET_KEY
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-+lxzy1i9g#m8pm_6^53a(ef7^i^b32fks)-pt2!4%n5o+bgq00'
)

# ── Mode debug ───────────────────────────────────────────────────────────────
# En production : DJANGO_DEBUG=False
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# ── Hôtes autorisés ─────────────────────────────────────────────────────────
# En production : DJANGO_ALLOWED_HOSTS=votredomaine.com www.votredomaine.com
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost 127.0.0.1').split()

# ── Sécurité HTTPS (actif uniquement en production) ─────────────────────────
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000       # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # SECURE_SSL_REDIRECT activé uniquement en production réelle (pas en test local)
    if os.environ.get('PRODUCTION') == 'True':
        SECURE_SSL_REDIRECT = True

# ── Applications ─────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "tailwind",
    "theme",
    'administration.apps.AdminConfig',
    'client',
    'livreur',
    'producteur',
]
#cette ligne dit a django l’app qui contient la configuration Tailwind s’appelle theme sinon Django ne sait pas où chercher Tailwind
TAILWIND_APP_NAME = "theme"

AUTH_USER_MODEL = 'administration.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Oblige à choisir un nouveau mot de passe après un mot de passe provisoire
    'administration.middleware.ChangementMotDePasseObligatoire',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'yessnaaconnect.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'yessnaaconnect.wsgi.application'

# ── Base de données ──────────────────────────────────────────────────────────
# Par défaut : SQLite. Pour PostgreSQL, définir DB_ENGINE=postgresql dans .env
if os.environ.get('DB_ENGINE') == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['DB_NAME'],
            'USER': os.environ['DB_USER'],
            'PASSWORD': os.environ['DB_PASSWORD'],
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ── Validation des mots de passe ─────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internationalisation ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Dakar'
USE_I18N = True
USE_TZ = True

# ── Fichiers statiques ────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ── Fichiers media (uploads) ──────────────────────────────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── E-mails (récupération de mot de passe) ───────────────────────────────────
# En production, renseigner dans .env (ex. boîte LWS noreply@yeesnaa.com) :
#   EMAIL_HOST=mail.yeesnaa.com  EMAIL_PORT=465  EMAIL_USE_SSL=True
#   EMAIL_HOST_USER=noreply@yeesnaa.com  EMAIL_HOST_PASSWORD=...
#   DEFAULT_FROM_EMAIL="YEESNAA CONNECT <noreply@yeesnaa.com>"
# Tester l'envoi : python manage.py sendtestemail adresse@exemple.com
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False') == 'True'
    EMAIL_USE_TLS = (not EMAIL_USE_SSL) and os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_TIMEOUT = 15
else:
    # Pas de serveur configuré : les e-mails sont écrits dans les logs (aucun envoi réel)
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'YEESNAA CONNECT <noreply@yeesnaa.com>')
EMAIL_ENVOI_ACTIF = bool(EMAIL_HOST)

# Lien de réinitialisation valable 1 heure
PASSWORD_RESET_TIMEOUT = 60 * 60

# Contact affiché quand la récupération par e-mail n'est pas possible
CONTACT_SUPPORT_TELEPHONE = os.environ.get('CONTACT_SUPPORT_TELEPHONE', '+221 77 545 15 99')
CONTACT_SUPPORT_EMAIL = os.environ.get('CONTACT_SUPPORT_EMAIL', 'yessalgicuun.pdg@gmail.com')
