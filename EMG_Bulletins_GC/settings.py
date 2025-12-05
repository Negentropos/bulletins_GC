"""
Django settings for EMG_Bulletins_GC project.
ADAPTÉ POUR GESTION HYBRIDE : LOCAL (.env) / PROD (config.json)
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# settings.py

# ... imports ...

# --- DÉTECTION DE L'ENVIRONNEMENT ---
CONFIG_PATH = '/etc/config.json'

if os.path.exists(CONFIG_PATH):
    # === MODE PRODUCTION (SERVEUR) ===
    with open(CONFIG_PATH) as config_file:
        config = json.load(config_file)

    SECRET_KEY = config.get('SECRET_KEY')
    DEBUG = False

    # C'est ici que ça change : on charge la liste depuis le JSON
    # Si le JSON ne contient pas la liste, on met une liste vide par sécurité
    ALLOWED_HOSTS = config.get('ALLOWED_HOSTS', [])

else:
    # === MODE LOCAL (DEV) ===
    load_dotenv(BASE_DIR / '.env')

    SECRET_KEY = os.getenv('SECRET_KEY', 'cle-par-defaut-si-pas-de-env')
    DEBUG = True
    # En local, on prend ce qu'il y a dans le .env ou localhost par défaut
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'authentication',
    'bulletins',
    'csvimport.app.CSVImportConf',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
]

ROOT_URLCONF = 'EMG_Bulletins_GC.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR.joinpath('templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'EMG_Bulletins_GC.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'assets')
STATICFILES_DIRS = [BASE_DIR.joinpath('static/')]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'authentication.User'
LOGIN_URL='login'
LOGIN_REDIRECT_URL = 'home'

# --- SÉCURITÉ CONDITIONNELLE ---
# On active ces protections UNIQUEMENT si DEBUG est False (donc en Prod)
if not DEBUG:
    SECURE_HSTS_SECONDS = 15780000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
else:
    # En local, on relâche tout pour éviter les blocages http/https
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False


# CSP - Content Security Policy
# Note : Peut parfois gêner en local selon les navigateurs, à surveiller.
CSP_DEFAULT_SRC = ("'none'", )
CSP_BASE_URI = ("'none'", )
CSP_FRAME_ANCESTORS = ("'none'", )
CSP_FORM_ACTION = ("'self'", )
CSP_STYLE_SRC = ("'self'",'fonts.googleapis.com','kit.fontawesome.com','cdn.jsdelivr.net')
CSP_SCRIPT_SRC = ("'self'", 'ajax.googleapis.com','code.jquery.com','kit.fontawesome.com', 'unpkg.com', 'cdn.jsdelivr.net')
CSP_IMG_SRC = ("'self'",'cdn.jsdelivr.net','data: w3.org/svg/2000')
CSP_FONT_SRC = ("'self'",'fonts.googleapis.com','cdn.jsdelivr.net','kit.fontawesome.com','fonts.gstatic.com')
CSP_INCLUDE_NONCE_IN = ("script-src", "style-src")