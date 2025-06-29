# agendamento_system/settings.py

from pathlib import Path
import os
from decouple import config

# --- CONFIGURAÇÕES BÁSICAS DO PROJETO ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- APLICAÇÕES INSTALADAS ---
# Adicione 'whitenoise.runserver_nostatic' se for usar o Whitenoise localmente também
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # Para servir arquivos estáticos em produção
    'django.contrib.staticfiles',
    'agendamentos.apps.AgendamentosConfig',
]

# --- MIDDLEWARE ---
# Whitenoise foi adicionado para servir os arquivos estáticos de forma eficiente
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Adicionado aqui
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

# --- LÓGICA DE AMBIENTE: PRODUÇÃO (GOOGLE CLOUD) vs DESENVOLVIMENTO (LOCAL) ---
IS_PRODUCTION = os.getenv('GAE_APPLICATION', None)

if IS_PRODUCTION:
    # --- CONFIGURAÇÕES DE PRODUÇÃO (GOOGLE APP ENGINE) ---
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = False
    
    # Configuração de hosts permitidos mais segura
    # Ele pega o ID do projeto do ambiente e constrói a URL automaticamente
    project_id = os.environ.get('GCP_PROJECT_ID')
    ALLOWED_HOSTS = [f'{project_id}.rj.r.appspot.com', f'{project_id}.uc.r.appspot.com']
    
    # Conexão para o Google Cloud SQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql', # Ou postgresql
            'HOST': f"/cloudsql/{os.environ.get('CLOUD_SQL_CONNECTION_NAME')}",
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'NAME': os.environ.get('DB_NAME'),
        }
    }
    # Segurança adicional
    CSRF_TRUSTED_ORIGINS = [f'https://{host}' for host in ALLOWED_HOSTS]
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

else:
    # --- CONFIGURAÇÕES DE DESENVOLVIMENTO (LOCAL) ---
    # As variáveis vêm do seu arquivo .env
    SECRET_KEY = config('SECRET_KEY')
    DEBUG = config('DEBUG', default=True, cast=bool)
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
    
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
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# --- CONFIGURAÇÃO DE E-MAIL (SENDGRID) ---
# Em produção, virá do app.yaml. Localmente, do .env.
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', config('SENDGRID_API_KEY', default=''))
if SENDGRID_API_KEY:
    EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
    DEFAULT_FROM_EMAIL = 'contato.barbeariachampions@gmail.com' # Use seu email aqui


# --- OUTRAS CONFIGURAÇÕES ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'agendamentos:painel'