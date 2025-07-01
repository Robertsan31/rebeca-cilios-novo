# agendamento_system/settings.py

from pathlib import Path
import os
from decouple import config

# --- CONFIGURAÇÕES BÁSICAS DO PROJETO ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- APLICAÇÕES INSTALADAS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', 
    'django.contrib.staticfiles',
    'agendamentos.apps.AgendamentosConfig',
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
    
    project_id = os.environ.get('GCP_PROJECT_ID')
    ALLOWED_HOSTS = [f'{project_id}.rj.r.appspot.com', f'{project_id}.uc.r.appspot.com']
    
    # ... (o resto das suas configurações de produção) ...

else:
    # --- CONFIGURAÇÕES DE DESENVOLVIMENTO (LOCAL) ---
    SECRET_KEY = config('SECRET_KEY')
    DEBUG = config('DEBUG', default=True, cast=bool)
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# --- VALIDAÇÃO DE SENHAS ---
AUTH_PASSWORD_VALIDATORS = [
    # ... (seus validadores) ...
]

# --- INTERNACIONALIZAÇÃO ---
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# --- ARQUIVOS ESTÁTICOS E DE MÍDIA ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# >>> ADIÇÃO PARA ARQUIVOS DE UPLOAD (MÍDIA) <<<
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# --- OUTRAS CONFIGURAÇÕES ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'agendamentos:painel'