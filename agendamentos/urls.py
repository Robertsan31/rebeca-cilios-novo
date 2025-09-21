from django.urls import path
from . import views

app_name = "agendamentos"

urlpatterns = [
    # Painel
    path("", views.painel, name="painel"),

    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/export/csv/", views.dashboard_export_csv, name="dashboard_export_csv"),
    path("dashboard/export/pdf/", views.dashboard_export_pdf, name="dashboard_export_pdf"),

    # Stats
    path("stats/", views.stats, name="stats"),
    path("stats/7d/", views.stats, name="stats_7d"),

    # APIs internas do painel (FullCalendar / horários / notificação)
    path("api/agendamentos/", views.api_agendamentos, name="api_agendamentos"),
    path("api/horarios/", views.api_horarios_disponiveis, name="api_horarios_disponiveis"),
    path("api/notificacao/", views.api_notificacao_proximo_agendamento, name="api_notificacao_proximo_agendamento"),

    # Fluxo de agendamento
    path("agendar/<int:servico_id>/", views.agendar_servico, name="agendar_servico"),
    path(
        "confirmar/<int:servico_id>/<int:year>/<int:month>/<int:day>/<int:hour>/<int:minute>/",
        views.confirmar_agendamento,
        name="confirmar_agendamento",
    ),

    # Gestão de Agendamentos
    path("agendamentos/", views.gerir_agendamentos, name="gerir_agendamentos"),
    path(
        "agendamentos/atualizar-status/<int:agendamento_id>/",
        views.atualizar_status_agendamento,
        name="atualizar_status_agendamento",
    ),

    # Serviços
    path("servicos/", views.gerir_servicos, name="gerir_servicos"),
    path("servicos/novo/", views.criar_servico, name="criar_servico"),
    path("servicos/editar/<int:servico_id>/", views.editar_servico, name="editar_servico"),
    path("servicos/excluir/<int:servico_id>/", views.excluir_servico, name="excluir_servico"),
    path("servicos/<int:servico_id>/remover-imagem/", views.remover_imagem_servico, name="remover_imagem_servico"),
    path("servicos/<int:servico_id>/recortar/", views.recortar_imagem_servico, name="recortar_imagem_servico"),

    # Imagens adicionais (até 5 por serviço)
    path(
        "servicos/<int:servico_id>/imagens/adicionar/",
        views.adicionar_imagens_adicionais,
        name="adicionar_imagens_adicionais",
    ),
    path(
        "servicos/imagens/<int:imagem_id>/remover/",
        views.remover_imagem_adicional,
        name="remover_imagem_adicional",
    ),

    # Resultados das Alunas (painel)
    path("resultados/", views.gerir_resultados, name="gerir_resultados"),
    path("resultados/novo/", views.criar_resultado, name="criar_resultado"),
    path("resultados/editar/<int:resultado_id>/", views.editar_resultado, name="editar_resultado"),
    path("resultados/excluir/<int:resultado_id>/", views.excluir_resultado, name="excluir_resultado"),

    # Prova Social (painel – separado dos resultados)
    path("provas/", views.gerir_provas, name="gerir_provas"),
    path("provas/novo/", views.criar_prova, name="criar_prova"),
    path("provas/editar/<int:prova_id>/", views.editar_prova, name="editar_prova"),
    path("provas/excluir/<int:prova_id>/", views.excluir_prova, name="excluir_prova"),

    # Clientes  ✅ (adicionados)
    path("clientes/", views.gerir_clientes, name="gerir_clientes"),
    path("clientes/novo/", views.criar_cliente, name="criar_cliente"),
    path("clientes/editar/<int:cliente_id>/", views.editar_cliente, name="editar_cliente"),
    path("clientes/excluir/<int:cliente_id>/", views.excluir_cliente, name="excluir_cliente"),

    # (opcional) rota de curso dentro do namespace do painel
    path("curso/", views.curso, name="curso"),
]
