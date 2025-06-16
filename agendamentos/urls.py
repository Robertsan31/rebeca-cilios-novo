# agendamentos/urls.py
from django.urls import path
from . import views

app_name = 'agendamentos'

urlpatterns = [
    # A raiz do painel
    path('', views.painel, name='painel'),
    
    # URLs da API (agora dentro do namespace 'agendamentos')
    path('api/agendamentos/', views.api_agendamentos, name='api_agendamentos'),
    path('api/notificacao/', views.api_notificacao_proximo_agendamento, name='api_notificacao_proximo_agendamento'),

    # As outras URLs do painel
    path('agendar/<int:servico_id>/', views.agendar_servico, name='agendar_servico'),
    path('confirmar/<int:servico_id>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/', views.confirmar_agendamento, name='confirmar_agendamento'),
    
    # Gerenciamento
    path('servicos/', views.gerir_servicos, name='gerir_servicos'),
    path('servicos/novo/', views.criar_servico, name='criar_servico'),
    path('servicos/editar/<int:servico_id>/', views.editar_servico, name='editar_servico'),
    path('servicos/excluir/<int:servico_id>/', views.excluir_servico, name='excluir_servico'),
    
    path('agendamentos/', views.gerir_agendamentos, name='gerir_agendamentos'),
    path('agendamentos/atualizar-status/<int:agendamento_id>/', views.atualizar_status_agendamento, name='atualizar_status_agendamento'),
    
    path('clientes/', views.gerir_clientes, name='gerir_clientes'),
    path('clientes/editar/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/excluir/<int:cliente_id>/', views.excluir_cliente, name='excluir_cliente'),
]
