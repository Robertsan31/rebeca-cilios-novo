from django.contrib import admin
from .models import Cliente, Servico, Agendamento


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "email", "telefone", "cpf", "data_cadastro")
    search_fields = ("nome", "email", "cpf", "telefone")
    list_filter = ("data_cadastro",)
    ordering = ("nome",)


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "preco", "duracao", "has_img")
    search_fields = ("nome", "descricao")
    list_filter = ("duracao",)
    ordering = ("id",)

    def has_img(self, obj):
        return bool(obj.imagem)
    has_img.boolean = True
    has_img.short_description = "Imagem?"

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ("id", "data_hora", "status", "cliente", "servico")
    search_fields = ("cliente__nome", "servico__nome")
    list_filter = ("status", "data_hora")
    date_hierarchy = "data_hora"
    ordering = ("-data_hora",)
