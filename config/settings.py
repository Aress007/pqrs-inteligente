"""
Configuración del proyecto PQRS-INTELIGENTE
Django - Proyecto Final SENA Cúcuta 2026
"""
import os
from pathlib import Path

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Cambiar esta clave antes de desplegar en producción
SECRET_KEY = 'django-insecure-2$gb5q@s0u&z4bw^1)!8q5-3%irr_-3=8-kr=b_oivan!#3%c3'

# En producción cambiar a False
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ===== APLICACIONES INSTALADAS =====
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

# ===== BASE DE DATOS =====
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ===== VALIDACIÓN DE CONTRASEÑAS =====
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===== INTERNACIONALIZACIÓN =====
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# ===== ARCHIVOS ESTÁTICOS =====
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ===== ARCHIVOS MEDIA (fotos de perfil, adjuntos PQRS) =====
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ===== AUTENTICACIÓN Y REDIRECCIONES =====
LOGIN_URL = '/usuarios/login/'
LOGIN_REDIRECT_URL = '/pqrs/dashboard/'
LOGOUT_REDIRECT_URL = '/usuarios/login/'

# ===== CAMPO PRIMARIO POR DEFECTO =====
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===== MENSAJES (para alertas éxito/error/info) =====
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG:   'debug',
    messages.INFO:    'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR:   'error',
}

# ===== CONFIGURACIÓN DE EPAYCO (Sandbox) =====
EPAYCO_PUBLIC_KEY = '2f21c65e4a491f917cf8be32228fea81'
EPAYCO_PRIVATE_KEY = '41a6598805ddd4463248b01a2afcf3bc'  
EPAYCO_P_CUST_ID_CLIENTE = '1586550'  # ID de cliente de prueba
EPAYCO_P_KEY = '56860f2288b54e51ea062b9785bad8db410380d5'  # P_KEY de prueba
EPAYCO_TEST = True  
EPAYCO_LANG = 'ES'

# ===== CONFIGURACIÓN DE CORREO PARA DESARROLLO =====
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'