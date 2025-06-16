# agendamento_system/settings.py

from pathlib import Path
import os
from decouple import config # Usamos para desenvolvimento local

# --- CONFIGURAÇÕES BÁSICAS DO PROJETO ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- CONFIGURAÇÕES DE SEGURANÇA E AMBIENTE ---
# Em produção, o SECRET_KEY virá do app.yaml. Localmente, do .env.
SECRET_KEY = os.environ.get('SECRET_KEY', config('SECRET_KEY'))

# O DEBUG será 'False' em produção (lido do app.yaml) e True localmente (lido do .env)
DEBUG = os.environ.get('DEBUG', config('DEBUG', default=True, cast=bool))

ALLOWED_HOSTS = ['*'] # Seguro para o App Engine


# --- APLICAÇÕES INSTALADAS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'agendamentos.apps.AgendamentosConfig',
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# --- CONFIGURAÇÕES DE URLS E TEMPLATES ---
ROOT_URLCONF = 'agendamento_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'agendamento_system.wsgi.application'


# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
# Lógica inteligente para alternar entre o banco de dados local e o da nuvem
if os.getenv('GAE_APPLICATION', None):
    # Conexão para o Google Cloud SQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': f"/cloudsql/{os.environ.get('CLOUD_SQL_CONNECTION_NAME')}",
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'NAME': os.environ.get('DB_NAME'),
        }
    }
else:
    # Configuração para desenvolvimento local com SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# --- VALIDAÇÃO DE SENHAS ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- INTERNACIONALIZAÇÃO ---
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# --- ARQUIVOS ESTÁTICOS ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# --- CONFIGURAÇÃO DE E-MAIL (SENDGRID) ---
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', config('SENDGRID_API_KEY'))
DEFAULT_FROM_EMAIL = 'contato.barbeariachampions@gmail.com'


# --- OUTRAS CONFIGURAÇÕES ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'agendamentos:painel'

