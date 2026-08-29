"""
Configuración del proyecto PQRS-INTELIGENTE
Django - Proyecto Final SENA Cúcuta 2026
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# CARGAR VARIABLES DE ENTORNO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-clave-solo-para-desarrollo'
)

DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        'ALLOWED_HOSTS',
        'localhost,127.0.0.1'
    ).split(',')
    if host.strip()
]


# ============================================================
# APLICACIONES INSTALADAS
# ============================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps del proyecto
    'core',
    'empresas',
    'pqrs',
    'usuarios',
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'config.urls'


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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


WSGI_APPLICATION = 'config.wsgi.application'


# ============================================================
# BASE DE DATOS
# ============================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ============================================================
# VALIDACIÓN DE CONTRASEÑAS
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator'
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator'
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator'
    },
]


# ============================================================
# INTERNACIONALIZACIÓN
# ============================================================

LANGUAGE_CODE = 'es-co'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = True


# ============================================================
# ARCHIVOS ESTÁTICOS
# ============================================================

STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'


# ============================================================
# ARCHIVOS MEDIA
# ============================================================

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'

DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880


# ============================================================
# AUTENTICACIÓN Y REDIRECCIONES
# ============================================================

LOGIN_URL = '/usuarios/login/'

LOGIN_REDIRECT_URL = '/pqrs/dashboard/'

LOGOUT_REDIRECT_URL = '/usuarios/login/'


# ============================================================
# CAMPO PRIMARIO POR DEFECTO
# ============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================
# MENSAJES
# ============================================================

from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}


# ============================================================
# EPAYCO
# ============================================================

EPAYCO_PUBLIC_KEY = os.getenv('EPAYCO_PUBLIC_KEY')

EPAYCO_PRIVATE_KEY = os.getenv('EPAYCO_PRIVATE_KEY')

EPAYCO_P_CUST_ID_CLIENTE = os.getenv(
    'EPAYCO_P_CUST_ID_CLIENTE'
)

EPAYCO_P_KEY = os.getenv('EPAYCO_P_KEY')

EPAYCO_TEST = os.getenv(
    'EPAYCO_TEST',
    'True'
).lower() == 'true'

EPAYCO_LANG = os.getenv(
    'EPAYCO_LANG',
    'ES'
)


# ============================================================
# CORREO (SendGrid)
# ============================================================

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
EMAIL_PORT = 587
EMAIL_USE_TLS = True

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'aresjq21@gmail.com')