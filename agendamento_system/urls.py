from django.contrib import admin
from django.urls import path, include
from agendamentos import views as agendamento_views
from agendamentos.views import logout_view
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Públicas
    path('', agendamento_views.home, name='home'),
    path('servicos/', agendamento_views.lista_servicos, name='lista_servicos'),
    path("curso/", agendamento_views.curso, name="curso"),  # << corrigido

    # Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='agendamentos/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),  # usando sua função customizada

    # APIs públicas
    path('api/agendamentos/', agendamento_views.api_agendamentos, name='api_agendamentos'),
    path('api/notificacao/', agendamento_views.api_notificacao_proximo_agendamento, name='api_notificacao_proximo_agendamento'),

    # Área autenticada
    path('painel/', include('agendamentos.urls', namespace='agendamentos')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
