# agendamentos/views.py
import json
import pytz 
from decimal import Decimal
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Servico, Agendamento, Cliente
from .forms import ClienteForm, ServicoForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q
from datetime import date, timedelta, time, datetime
from django.core.mail import send_mail
from django.conf import settings

# --- Views Públicas ---

def home(request):
    return render(request, 'agendamentos/home.html')

def lista_servicos(request):
    servicos = Servico.objects.all().order_by('nome')
    context = {'servicos': servicos}
    return render(request, 'agendamentos/lista_servicos.html', context)


# --- Funções Auxiliares e API ---

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)

@login_required
def api_agendamentos(request):
    agendamentos = Agendamento.objects.select_related('cliente', 'servico').all()
    eventos = []
    color_map = { "Confirmado": "#a389cc", "Cancelado": "#a0a0a0", "Realizado": "#5cb85c", }
    for agendamento in agendamentos:
        cor_evento = color_map.get(agendamento.status, "#5bc0de")
        duracao_padrao_minutos = 60 
        eventos.append({
            'id': agendamento.id, 'title': f'{agendamento.cliente.nome}',
            'start': agendamento.data_hora.isoformat(),
            'end': (agendamento.data_hora + timedelta(minutes=duracao_padrao_minutos)).isoformat(), 
            'color': cor_evento,
            'extendedProps': {
                'servico_nome': agendamento.servico.nome, 'cliente_nome': agendamento.cliente.nome,
                'cliente_telefone': agendamento.cliente.telefone, 'cliente_email': agendamento.cliente.email,
                'status': agendamento.status,
            }
        })
    return JsonResponse(eventos, safe=False)

@login_required
def api_notificacao_proximo_agendamento(request):
    timezone = pytz.timezone(settings.TIME_ZONE)
    agora = datetime.now(timezone)
    limite = agora + timedelta(minutes=15)
    proximo_agendamento = Agendamento.objects.filter(
        data_hora__gte=agora, data_hora__lte=limite, status='Confirmado'
    ).order_by('data_hora').first()
    if proximo_agendamento:
        data = { 'notificacao': True, 'cliente': proximo_agendamento.cliente.nome, 'servico': proximo_agendamento.servico.nome, 'horario': proximo_agendamento.data_hora.astimezone(timezone).strftime('%H:%M')}
    else:
        data = {'notificacao': False}
    return JsonResponse(data)


# --- Views do Painel de Controle (Privadas) ---

@login_required
def painel(request):
    servicos = Servico.objects.all().values('id', 'nome', 'preco')
    servicos_json = json.dumps(list(servicos), cls=DecimalEncoder)
    context = {'servicos_json': servicos_json}
    return render(request, 'agendamentos/painel.html', context)

@login_required
def agendar_servico(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id)
    str_data_selecionada = request.GET.get('data', date.today().strftime('%Y-%m-%d'))
    dia_selecionado = datetime.strptime(str_data_selecionada, '%Y-%m-%d').date()
    horario_inicio = time(9, 0)
    horario_fim = time(18, 0)
    agendamentos_no_dia = Agendamento.objects.filter(data_hora__date=dia_selecionado, status='Confirmado')
    horarios_ocupados = [ag.data_hora.time() for ag in agendamentos_no_dia]
    horarios_disponiveis = []
    slot_atual = datetime.combine(dia_selecionado, horario_inicio)
    fim_dia = datetime.combine(dia_selecionado, horario_fim)
    duracao_servico_minutos = 60
    while slot_atual < fim_dia:
        if slot_atual.time() not in horarios_ocupados and slot_atualmente > datetime.now():
            horarios_disponiveis.append(slot_atual.time())
        slot_atual += timedelta(minutes=duracao_servico_minutos)
    context = {'servico': servico, 'horarios_disponiveis': horarios_disponiveis, 'dia_selecionado': dia_selecionado}
    return render(request, 'agendamentos/agendar_servico.html', context)

@login_required
def confirmar_agendamento(request, servico_id, year, month, day, hour, minute):
    servico = get_object_or_404(Servico, id=servico_id)
    data_hora_agendamento = datetime(year, month, day, hour, minute)
    if Agendamento.objects.filter(data_hora=data_hora_agendamento, status='Confirmado').exists():
        messages.error(request, 'Ops! Este horário já está ocupado por um agendamento confirmado.')
        return redirect('agendamentos:painel')
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        cliente_origem = request.POST.get('cliente_origem')
        cliente = None
        if cliente_origem == 'existente':
            cliente_id = request.POST.get('cliente_id')
            if not cliente_id:
                messages.error(request, 'Você precisa selecionar uma cliente existente.')
            else:
                cliente = get_object_or_404(Cliente, id=cliente_id)
        elif cliente_origem == 'novo':
            if form.is_valid():
                try:
                    cliente = form.save()
                    messages.success(request, f'Cliente "{cliente.nome}" cadastrada com sucesso!')
                except IntegrityError:
                    messages.error(request, 'Não foi possível cadastrar. Verifique se o CPF ou e-mail já existem.')
                    cliente = None
            else:
                for field, error_list in form.errors.items():
                    messages.error(request, f"Erro no campo '{form.fields[field].label}': {error_list[0]}")
        if cliente:
            novo_agendamento = Agendamento.objects.create(cliente=cliente, servico=servico, data_hora=data_hora_agendamento, status='Confirmado')
            try:
                assunto_cliente = f"Confirmação de Agendamento - BellCilios"
                data_formatada = novo_agendamento.data_hora.strftime('%d/%m/%Y às %H:%M')
                mensagem_cliente = (f"Olá, {cliente.nome}!\n\nSeu agendamento para '{servico.nome}' foi confirmado para {data_formatada}.\n\nAtenciosamente,\nEquipe BellCilios")
                send_mail(assunto_cliente, mensagem_cliente, settings.DEFAULT_FROM_EMAIL, [cliente.email])
                assunto_dono = f"Novo Agendamento: {servico.nome} para {cliente.nome}"
                mensagem_dono = (f"Novo agendamento realizado:\n\nCliente: {cliente.nome}\nTelefone: {cliente.telefone}\nServiço: {servico.nome}\nData e Hora: {data_formatada}")
                send_mail(assunto_dono, mensagem_dono, settings.DEFAULT_from_email, [settings.DEFAULT_FROM_EMAIL])
            except Exception as e:
                print(f"ERRO AO ENVIAR E-MAIL DE CONFIRMAÇÃO: {e}")
                messages.warning(request, 'Agendamento confirmado, mas houve um erro ao enviar o e-mail.')
            messages.success(request, f'Agendamento para {cliente.nome} confirmado com sucesso!')
            return redirect('agendamentos:painel')
    clientes = Cliente.objects.all().order_by('nome')
    form = ClienteForm()
    context = {'servico': servico, 'data_hora': data_hora_agendamento, 'clientes': clientes, 'form': form}
    return render(request, 'agendamentos/confirmar_agendamento.html', context)

@login_required
def gerir_servicos(request):
    servicos = Servico.objects.all().order_by('nome')
    context = {'servicos': servicos}
    return render(request, 'agendamentos/gerir_servicos.html', context)

@login_required
def criar_servico(request):
    if request.method == 'POST':
        form = ServicoForm(request.POST, request.FILES) # request.FILES ESTÁ AQUI
        if form.is_valid():
            form.save()
            messages.success(request, 'Serviço adicionado com sucesso!')
            return redirect('agendamentos:gerir_servicos')
    else:
        form = ServicoForm()
    context = {'form': form, 'titulo_pagina': 'Adicionar Novo Serviço'}
    return render(request, 'agendamentos/criar_editar_servico.html', context)

@login_required
def editar_servico(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id)
    if request.method == 'POST':
        form = ServicoForm(request.POST, request.FILES, instance=servico) # request.FILES ESTÁ AQUI
        if form.is_valid():
            form.save()
            messages.success(request, 'Serviço atualizado com sucesso!')
            return redirect('agendamentos:gerir_servicos')
    else:
        form = ServicoForm(instance=servico)
    context = {'form': form, 'titulo_pagina': f'Editar Serviço: {servico.nome}'}
    return render(request, 'agendamentos/criar_editar_servico.html', context)

import os
from django.conf import settings

@login_required
def excluir_servico(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id)
    if request.method == 'POST':
        nome_servico = servico.nome

        # Apaga o arquivo da imagem se existir
        if servico.imagem and os.path.isfile(servico.imagem.path):
            os.remove(servico.imagem.path)

        servico.delete()
        messages.success(request, f'Serviço "{nome_servico}" excluído com sucesso!')
        return redirect('agendamentos:gerir_servicos')
    
    context = {'servico': servico}
    return render(request, 'agendamentos/excluir_servico_confirm.html', context)


@login_required
def gerir_agendamentos(request):
    str_dia_selecionado = request.GET.get('data', date.today().strftime('%Y-%m-%d'))
    dia = datetime.strptime(str_dia_selecionado, '%Y-%m-%d').date()
    agendamentos = Agendamento.objects.filter(data_hora__date=dia).order_by('data_hora')
    context = {'agendamentos': agendamentos, 'dia_selecionado': dia}
    return render(request, 'agendamentos/gerir_agendamentos.html', context)

@login_required
@require_POST
def atualizar_status_agendamento(request, agendamento_id):
    agendamento = get_object_or_404(Agendamento, id=agendamento_id)
    novo_status = request.POST.get('status')
    if novo_status in ['Confirmado', 'Cancelado', 'Realizado']:
        agendamento.status = novo_status
        agendamento.save()
        messages.success(request, f'O status do agendamento de {agendamento.cliente.nome} foi atualizado para "{novo_status}".')
    else:
        messages.error(request, 'Status inválido.')
    data_str = agendamento.data_hora.strftime('%Y-%m-%d')
    return redirect(f"{reverse('agendamentos:gerir_agendamentos')}?data={data_str}")

@login_required
def gerir_clientes(request):
    query = request.GET.get('q')
    if query:
        clientes = Cliente.objects.filter(Q(nome__icontains=query) | Q(email__icontains=query) | Q(cpf__icontains=query)).order_by('nome')
    else:
        clientes = Cliente.objects.all().order_by('nome')
    context = {'clientes': clientes, 'query': query}
    return render(request, 'agendamentos/gerir_clientes.html', context)

@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('agendamentos:gerir_clientes')
    else:
        form = ClienteForm(instance=cliente)
    context = {'form': form, 'titulo_pagina': f'Editar Cliente: {cliente.nome}'}
    return render(request, 'agendamentos/criar_editar_cliente.html', context)

@login_required
def excluir_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        nome_cliente = cliente.nome
        cliente.delete()
        messages.success(request, f'Cliente "{nome_cliente}" excluído com sucesso!')
        return redirect('agendamentos:gerir_clientes')
    context = {'cliente': cliente}
    return render(request, 'agendamentos/excluir_cliente_confirm.html', context)