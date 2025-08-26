# agendamento_system/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from agendamentos import views as agendamento_views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # --- Admin ---
    path('admin/', admin.site.urls),

    # --- URLs públicas ---
    path('', agendamento_views.home, name='home'),
    path('servicos/', agendamento_views.lista_servicos, name='lista_servicos'),

    # --- Autenticação ---
    path('login/', auth_views.LoginView.as_view(template_name='agendamentos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # --- APIs públicas ---
    path('api/agendamentos/', agendamento_views.api_agendamentos, name='api_agendamentos'),
    path('api/notificacao/', agendamento_views.api_notificacao_proximo_agendamento, name='api_notificacao_proximo_agendamento'),

    # --- Painel (área autenticada) ---
    path('painel/', include('agendamentos.urls', namespace='agendamentos')),
]

# Servir arquivos de mídia em DEV
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# agendamento_system/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from agendamentos import views as agendamento_views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # --- Admin ---
    path('admin/', admin.site.urls),

    # --- URLs públicas ---
    path('', agendamento_views.home, name='home'),
    path('servicos/', agendamento_views.lista_servicos, name='lista_servicos'),

    # --- Autenticação ---
    path('login/', auth_views.LoginView.as_view(template_name='agendamentos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # --- APIs públicas ---
    path('api/agendamentos/', agendamento_views.api_agendamentos, name='api_agendamentos'),
    path('api/notificacao/', agendamento_views.api_notificacao_proximo_agendamento, name='api_notificacao_proximo_agendamento'),

    # --- Painel (área autenticada) ---
    path('painel/', include('agendamentos.urls', namespace='agendamentos')),
]

# Servir arquivos de mídia em DEV
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
