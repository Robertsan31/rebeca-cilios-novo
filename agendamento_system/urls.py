from django.contrib import admin
from django.urls import path, include
from agendamentos import views as agendamento_views
from django.contrib.auth.views import LogoutView, LoginView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Páginas públicas
    path('', agendamento_views.home, name='home'),
    path('servicos/', agendamento_views.lista_servicos, name='lista_servicos'),
    path('curso/', agendamento_views.curso, name='curso'),
    path('resultados/', agendamento_views.resultados_alunas, name='resultados_alunas'),

    # Autenticação
    path(
        'login/',
        LoginView.as_view(
            template_name='agendamentos/login.html',
            redirect_authenticated_user=True
        ),
        name='login'
    ),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),

    # APIs públicas (sessão-dependentes mas fora do /painel/)
    path('api/notificacao/', agendamento_views.api_notificacao_proximo_agendamento,
         name='api_notificacao_proximo_agendamento'),

    # Área autenticada (painel)
    path('painel/', include('agendamentos.urls', namespace='agendamentos')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
