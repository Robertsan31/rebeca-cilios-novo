# agendamentos/admin.py
from django.contrib import admin
from .models import Cliente, Servico, Agendamento

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'telefone', 'cpf')
    search_fields = ('nome', 'email', 'cpf')

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    # CORREÇÃO: Removido 'duracao' da lista abaixo
    list_display = ('nome', 'preco')
    search_fields = ('nome',)

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'servico', 'data_hora', 'status')
    list_filter = ('status', 'servico')
    search_fields = ('cliente__nome', 'servico__nome')
    list_editable = ('status',)