from django.urls import path
from . import views

app_name = "agendamentos"

urlpatterns = [
    path("", views.painel, name="painel"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/export/csv/", views.dashboard_export_csv, name="dashboard_export_csv"),
    path("dashboard/export/pdf/", views.dashboard_export_pdf, name="dashboard_export_pdf"),

    path("stats/", views.stats, name="stats"),
    path("stats/7d/", views.stats, name="stats_7d"),

    path("api/agendamentos/", views.api_agendamentos, name="api_agendamentos"),
    path("api/notificacao/", views.api_notificacao_proximo_agendamento, name="api_notificacao_proximo_agendamento"),
    path("api/horarios/", views.api_horarios_disponiveis, name="api_horarios_disponiveis"),

    path("agendar/<int:servico_id>/", views.agendar_servico, name="agendar_servico"),
    path("confirmar/<int:servico_id>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/",
         views.confirmar_agendamento, name="confirmar_agendamento"),

    path("agendamentos/", views.gerir_agendamentos, name="gerir_agendamentos"),
    path("agendamentos/atualizar-status/<int:agendamento_id>/",
         views.atualizar_status_agendamento, name="atualizar_status_agendamento"),

    path("servicos/", views.gerir_servicos, name="gerir_servicos"),
    path("servicos/novo/", views.criar_servico, name="criar_servico"),
    path("servicos/editar/<int:servico_id>/", views.editar_servico, name="editar_servico"),
    path("servicos/excluir/<int:servico_id>/", views.excluir_servico, name="excluir_servico"),
    path("servicos/<int:servico_id>/remover-imagem/", views.remover_imagem_servico, name="remover_imagem_servico"),
    path("servicos/<int:servico_id>/recortar/", views.recortar_imagem_servico, name="recortar_imagem_servico"),

    path("clientes/", views.gerir_clientes, name="gerir_clientes"),
    path("clientes/editar/<int:cliente_id>/", views.editar_cliente, name="editar_cliente"),
    path("clientes/excluir/<int:cliente_id>/", views.excluir_cliente, name="excluir_cliente"),
]
