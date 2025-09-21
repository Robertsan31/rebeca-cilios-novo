# agendamentos/views.py
from __future__ import annotations

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django import forms

from datetime import timedelta, datetime, time
from io import BytesIO
import base64
import json

from .models import (
    Cliente, Servico, Agendamento,
    ResultadoAluna, ProvaSocial
)

# --------------------------------------------------------------------
# (Opcional) suporte a imagens adicionais se existir o model no projeto
# --------------------------------------------------------------------
try:
    from .models import ServicoImagem  # se não existir, fica como None
except Exception:
    ServicoImagem = None  # type: ignore


# --------------------------------------------------------------------
# Forms
# --------------------------------------------------------------------
class AgendamentoForm(forms.ModelForm):
    data_hora_agendamento = forms.CharField(
        label="Data e hora (YYYY-MM-DD HH:MM)",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    class Meta:
        model = Agendamento
        fields = []


# ============================================================
# PÚBLICO
# ============================================================

def home(request):
    # carrega provas sociais ativas para o bloco da home (se o template usar)
    provas = ProvaSocial.objects.filter(ativo=True).order_by("ordem", "-criado_em")[:8]
    return render(request, "agendamentos/home.html", {"provas": provas})


def lista_servicos(request):
    servicos = Servico.objects.all().order_by("nome")
    return render(request, "agendamentos/lista_servicos.html", {"servicos": servicos})


def curso(request):
    return render(request, "agendamentos/curso.html")


def resultados_alunas(request):
    resultados = ResultadoAluna.objects.filter(ativo=True).order_by("-criado_em")
    return render(request, "agendamentos/resultados_alunas.html", {"resultados": resultados})


# ============================================================
# ÁREA LOGADA
# ============================================================

@login_required
def painel(request):
    cliente = None
    if request.user and request.user.email:
        cliente = Cliente.objects.filter(email=request.user.email).first()

    agendamentos_pendentes = Agendamento.objects.none()
    agendamentos_confirmados = Agendamento.objects.none()

    if cliente:
        agendamentos_pendentes = Agendamento.objects.filter(
            cliente=cliente, status="Pendente"
        ).order_by("data_hora")
        agendamentos_confirmados = Agendamento.objects.filter(
            cliente=cliente, status="Confirmado"
        ).order_by("data_hora")

    qs = Servico.objects.values("id", "nome", "preco", "duracao").order_by("nome")
    servicos_list = [
        {"id": s["id"], "nome": s["nome"], "preco": float(s["preco"]), "duracao": s["duracao"]}
        for s in qs
    ]

    context = {
        "agendamentos_pendentes": agendamentos_pendentes,
        "agendamentos_confirmados": agendamentos_confirmados,
        "servicos_json": json.dumps(servicos_list, ensure_ascii=False),
    }
    return render(request, "agendamentos/painel.html", context)


@login_required
def dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("agendamentos:painel")

    total_servicos = Servico.objects.count()
    total_agendamentos = Agendamento.objects.count()
    agendamentos_pendentes = Agendamento.objects.filter(status="Pendente").count()
    agendamentos_confirmados = Agendamento.objects.filter(status="Confirmado").count()
    agendamentos_concluidos = Agendamento.objects.filter(status="Realizado").count()

    servicos_populares = (
        Servico.objects.annotate(num_agendamentos=Count("agendamentos"))
        .order_by("-num_agendamentos")[:5]
    )

    context = {
        "total_servicos": total_servicos,
        "total_agendamentos": total_agendamentos,
        "agendamentos_pendentes": agendamentos_pendentes,
        "agendamentos_confirmados": agendamentos_confirmados,
        "agendamentos_concluidos": agendamentos_concluidos,
        "servicos_populares": servicos_populares,
    }
    return render(request, "agendamentos/dashboard.html", context)


# ============================================================
# CLIENTES
# ============================================================

@login_required
def gerir_clientes(request):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar clientes.")
        return redirect("agendamentos:painel")

    q = request.GET.get("q", "").strip()
    clientes = Cliente.objects.all().order_by("nome")
    if q:
        clientes = clientes.filter(nome__icontains=q) | clientes.filter(email__icontains=q) | clientes.filter(cpf__icontains=q)

    return render(
        request,
        "agendamentos/gerir_clientes.html",
        {"clientes": clientes, "query": q},
    )


@login_required
def criar_cliente(request):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para criar clientes.")
        return redirect("agendamentos:painel")

    if request.method == "POST":
        nome = request.POST.get("nome", "").strip()
        email = request.POST.get("email", "").strip()
        telefone = request.POST.get("telefone", "").strip()
        cpf = request.POST.get("cpf", "").strip() or None

        if cpf and Cliente.objects.filter(cpf=cpf).exists():
            messages.error(request, "Já existe um cliente com esse CPF.")
        elif email and Cliente.objects.filter(email=email).exists():
            messages.error(request, "Já existe um cliente com esse e-mail.")
        else:
            Cliente.objects.create(nome=nome, email=email, telefone=telefone, cpf=cpf)
            messages.success(request, f"Cliente {nome} cadastrado com sucesso!")
            return redirect("agendamentos:gerir_clientes")

    return render(
        request,
        "agendamentos/criar_editar_cliente.html",
        {"titulo": "Novo Cliente"},
    )


@login_required
def editar_cliente(request, cliente_id: int):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para editar clientes.")
        return redirect("agendamentos:painel")

    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == "POST":
        cliente.nome = request.POST.get("nome", "").strip()
        cliente.email = request.POST.get("email", "").strip()
        cliente.telefone = request.POST.get("telefone", "").strip()
        cliente.cpf = request.POST.get("cpf", "").strip() or None
        try:
            cliente.save()
            messages.success(request, "Cliente atualizado com sucesso!")
            return redirect("agendamentos:gerir_clientes")
        except Exception as e:
            messages.error(request, f"Erro ao atualizar cliente: {e}")

    return render(
        request,
        "agendamentos/criar_editar_cliente.html",
        {"titulo": "Editar Cliente", "cliente": cliente},
    )


@login_required
def excluir_cliente(request, cliente_id: int):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para excluir clientes.")
        return redirect("agendamentos:painel")

    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == "POST":
        nome = cliente.nome
        cliente.delete()
        messages.success(request, f"Cliente {nome} excluído com sucesso!")
        return redirect("agendamentos:gerir_clientes")

    return render(request, "agendamentos/excluir_cliente_confirm.html", {"cliente": cliente})


# ============================================================
# EXPORTS (CSV/PDF)
# ============================================================

@login_required
def dashboard_export_csv(request):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("agendamentos:painel")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="agendamentos_dashboard.csv"'

    import csv
    writer = csv.writer(response)
    writer.writerow(["Serviço", "Cliente", "Data e Hora", "Status"])

    agendamentos = Agendamento.objects.select_related("servico", "cliente").order_by("data_hora")
    for ag in agendamentos:
        writer.writerow([
            ag.servico.nome if ag.servico else "—",
            ag.cliente.nome if ag.cliente else "—",
            timezone.localtime(ag.data_hora).strftime("%Y-%m-%d %H:%M"),
            ag.status,
        ])
    return response


@login_required
def dashboard_export_pdf(request):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("agendamentos:painel")

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
    except Exception:
        messages.error(request, "Biblioteca 'reportlab' não instalada. Rode: pip install reportlab")
        return redirect("agendamentos:dashboard")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Relatório de Agendamentos", styles["Title"]))
    elements.append(Paragraph(timezone.now().strftime("Gerado em %d/%m/%Y %H:%M"), styles["Normal"]))
    elements.append(Paragraph("<br/>", styles["Normal"]))

    data = [["Serviço", "Cliente", "Data e Hora", "Status"]]
    ags = Agendamento.objects.select_related("servico", "cliente").order_by("data_hora")
    for ag in ags:
        data.append([
            ag.servico.nome if ag.servico else "—",
            ag.cliente.nome if ag.cliente else "—",
            timezone.localtime(ag.data_hora).strftime("%Y-%m-%d %H:%M"),
            ag.status,
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return HttpResponse(buffer, content_type="application/pdf")


# ============================================================
# STATS / APIs
# ============================================================

@login_required
def stats(request):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("agendamentos:painel")

    hoje = timezone.localdate()
    inicio = hoje - timedelta(days=6)

    qs = (
        Agendamento.objects.filter(data_hora__date__gte=inicio, data_hora__date__lte=hoje)
        .values("data_hora__date")
        .annotate(count=Count("id"))
        .order_by("data_hora__date")
    )
    datas = [(inicio + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    mapa = {item["data_hora__date"].strftime("%Y-%m-%d"): item["count"] for item in qs}
    dados = [mapa.get(d, 0) for d in datas]

    return render(request, "agendamentos/stats.html", {"datas": datas, "dados_grafico": dados})


@login_required
def api_agendamentos(request):
    qs = Agendamento.objects.select_related("servico", "cliente").order_by("data_hora")
    if not request.user.is_staff:
        cliente = None
        if request.user.email:
            cliente = Cliente.objects.filter(email=request.user.email).first()
        qs = qs.filter(cliente=cliente) if cliente else qs.none()

    def palette(status: str):
        s = (status or "").lower()
        if s == "confirmado":
            return {"color": "#16a34a", "textColor": "#ffffff", "borderColor": "#15803d"}
        if s == "pendente":
            return {"color": "#2563eb", "textColor": "#ffffff", "borderColor": "#1d4ed8"}
        if s == "cancelado":
            return {"color": "#dc2626", "textColor": "#ffffff", "borderColor": "#b91c1c"}
        if s == "realizado":
            return {"color": "#9333ea", "textColor": "#ffffff", "borderColor": "#7e22ce"}
        return {"color": "#6b7280", "textColor": "#ffffff", "borderColor": "#4b5563"}

    data = []
    for ag in qs:
        dur = ag.servico.duracao if ag.servico else 60
        pal = palette(ag.status)
        data.append({
            "id": ag.id,
            "title": f"{ag.servico.nome if ag.servico else 'Serviço'} - {ag.cliente.nome if ag.cliente else 'Cliente'}",
            "start": timezone.localtime(ag.data_hora).isoformat(),
            "end": timezone.localtime(ag.data_hora + timedelta(minutes=dur)).isoformat(),
            "status": ag.status,
            **pal,
            "extendedProps": {
                "status": ag.status,
                "servico_nome": ag.servico.nome if ag.servico else "",
                "servico_id": ag.servico.id if ag.servico else None,
                "cliente_nome": ag.cliente.nome if ag.cliente else "",
                "cliente_email": ag.cliente.email if ag.cliente else "",
                "cliente_telefone": ag.cliente.telefone if ag.cliente else "",
            },
        })
    return JsonResponse(data, safe=False)


@login_required
def api_notificacao_proximo_agendamento(request):
    cliente = None
    if request.user and request.user.email:
        cliente = Cliente.objects.filter(email=request.user.email).first()

    if not cliente:
        return JsonResponse({"message": "Nenhuma notificação no momento."})

    proximo = (
        Agendamento.objects.filter(
            cliente=cliente,
            data_hora__gte=timezone.now(),
            status__in=["Pendente", "Confirmado"],
        )
        .order_by("data_hora")
        .first()
    )

    if proximo:
        restante = proximo.data_hora - timezone.now()
        if timedelta(0) < restante < timedelta(minutes=30):
            msg = f"Seu próximo agendamento de {proximo.servico.nome if proximo.servico else 'Serviço'} é em {int(restante.total_seconds()//60)} minutos."
            return JsonResponse({"message": msg})

    return JsonResponse({"message": "Nenhuma notificação no momento."})


@login_required
def api_horarios_disponiveis(request):
    """
    Retorna horários de um dia.
    - Se receber ?servico_id=..., usa a duração do serviço.
    - Se NÃO receber, usa 60 min (compatível com o flyout do calendário).
    Resposta inclui:
      { "slots": [ {"hora":"09:00", "ocupado": false}, ... ],
        "horarios": ["09:00","09:30", ...]  # apenas os livres (compat legada)
      }
    """
    data_str = request.GET.get("data", "")
    if not data_str:
        return JsonResponse({"error": "Data inválida."}, status=400)

    try:
        data_sel = datetime.strptime(data_str, "%Y-%m-%d").date()
    except Exception:
        return JsonResponse({"error": "Data inválida."}, status=400)

    # duração: por serviço (se informado) ou 60
    dur = 60
    servico_id = request.GET.get("servico_id")
    if servico_id:
        try:
            servico = get_object_or_404(Servico, id=int(servico_id))
            dur = int(servico.duracao or 60)
        except Exception:
            dur = 60

    horario_abre = time(9, 0)
    horario_fecha = time(18, 0)
    intervalo = 30

    slots = []
    horarios_livres = []

    atual = datetime.combine(data_sel, horario_abre)
    limite = datetime.combine(data_sel, horario_fecha)
    now_local = timezone.localtime()

    while atual + timedelta(minutes=dur) <= limite:
        # bloqueia passado do dia atual
        if data_sel == now_local.date() and atual <= now_local:
            atual += timedelta(minutes=intervalo)
            continue

        conflito = Agendamento.objects.filter(
            data_hora__date=data_sel,
            data_hora__lt=atual + timedelta(minutes=dur),
            data_hora__gte=atual - timedelta(minutes=dur),
            status__in=["Pendente", "Confirmado"],
        ).exists()

        hora_txt = atual.strftime("%H:%M")
        slots.append({"hora": hora_txt, "ocupado": bool(conflito)})
        if not conflito:
            horarios_livres.append(hora_txt)

        atual += timedelta(minutes=intervalo)

    return JsonResponse({"slots": slots, "horarios": horarios_livres})


# ============================================================
# AGENDAMENTOS (fluxo)
# ============================================================

@login_required
def agendar_servico(request, servico_id: int):
    servico = get_object_or_404(Servico, id=servico_id)
    if request.method == "POST":
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            raw = form.cleaned_data["data_hora_agendamento"]
            try:
                dt = timezone.make_aware(datetime.strptime(raw, "%Y-%m-%d %H:%M"))
            except Exception:
                messages.error(request, "Formato de data/hora inválido (use YYYY-MM-DD HH:MM).")
                return render(request, "agendamentos/agendar_servico.html", {"servico": servico, "config": None, "form": form})

            if dt <= timezone.now():
                messages.error(request, "Não é possível agendar em um horário que já passou.")
                return render(request, "agendamentos/agendar_servico.html", {"servico": servico, "config": None, "form": form})

            conflito = Agendamento.objects.filter(
                data_hora__date=dt.date(),
                data_hora__lt=dt + timedelta(minutes=servico.duracao),
                data_hora__gte=dt - timedelta(minutes=servico.duracao),
                status__in=["Pendente", "Confirmado"],
            ).exists()
            if conflito:
                messages.error(request, "Este horário não está mais disponível. Escolha outro.")
                return render(request, "agendamentos/agendar_servico.html", {"servico": servico, "config": None, "form": form})

            cliente = Cliente.objects.filter(email=request.user.email).first()

            ag = Agendamento.objects.create(
                servico=servico,
                cliente=cliente,
                data_hora=dt,
                status="Pendente",
            )
            messages.success(request, f"Agendamento #{ag.id} criado! Aguardando confirmação.")
            return redirect("agendamentos:painel")
    else:
        form = AgendamentoForm()

    return render(request, "agendamentos/agendar_servico.html", {"servico": servico, "config": None, "form": form})


@login_required
def confirmar_agendamento(request, servico_id: int, year: int, month: int, day: int, hour: int, minute: int):
    servico = get_object_or_404(Servico, id=servico_id)
    data_hora = timezone.make_aware(datetime(year, month, day, hour, minute))

    if data_hora <= timezone.now():
        messages.error(request, "Não é possível confirmar um agendamento que já passou.")
        return redirect("agendamentos:agendar_servico", servico_id=servico.id)

    conflito = Agendamento.objects.filter(
        data_hora__date=data_hora.date(),
        data_hora__lt=data_hora + timedelta(minutes=servico.duracao),
        data_hora__gte=data_hora - timedelta(minutes=servico.duracao),
        status__in=["Pendente", "Confirmado"],
    ).exists()
    if conflito:
        messages.error(request, "Este horário não está mais disponível. Escolha outro.")
        return redirect("agendamentos:agendar_servico", servico_id=servico.id)

    if request.method == "POST":
        cliente = Cliente.objects.filter(email=request.user.email).first()
        Agendamento.objects.create(
            servico=servico,
            cliente=cliente,
            data_hora=data_hora,
            status="Pendente",
        )
        messages.success(request, "Agendamento criado com sucesso! Aguardando confirmação.")
        return redirect("agendamentos:painel")

    return render(request, "agendamentos/confirmar_agendamento.html", {"servico": servico, "data_hora": data_hora})


@login_required
def gerir_agendamentos(request):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("agendamentos:painel")

    agendamentos = Agendamento.objects.select_related("servico", "cliente").order_by("data_hora")
    return render(request, "agendamentos/gerir_agendamentos.html", {"agendamentos": agendamentos})


@login_required
def atualizar_status_agendamento(request, agendamento_id: int):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para realizar esta ação.")
        return redirect("agendamentos:painel")

    ag = get_object_or_404(Agendamento, id=agendamento_id)
    if request.method == "POST":
        novo = request.POST.get("status", "")
        if novo in [choice[0] for choice in Agendamento.STATUS_CHOICES]:
            ag.status = novo
            ag.save()
            messages.success(request, f"Status do agendamento #{ag.id} atualizado para {novo}.")
        else:
            messages.error(request, "Status inválido.")
    return redirect("agendamentos:gerir_agendamentos")


# ============================================================
# SERVIÇOS
# ============================================================

@login_required
def gerir_servicos(request):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("agendamentos:painel")

    servicos = Servico.objects.all().order_by("nome")
    return render(request, "agendamentos/gerir_servicos.html", {"servicos": servicos})


from .forms import ServicoForm

@login_required
def criar_servico(request):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para criar serviços.")
        return redirect("agendamentos:painel")

    if request.method == "POST":
        form = ServicoForm(request.POST, request.FILES)
        if form.is_valid():
            servico = form.save(commit=False)

            imagem_base64 = request.POST.get("imagem_base64")
            if imagem_base64:
                try:
                    header, data64 = imagem_base64.split(";base64,")
                    ext = header.split("/")[-1]
                    data = base64.b64decode(data64)
                    from django.core.files.base import ContentFile
                    servico.imagem.save(f"servico_{servico.nome}.{ext}", ContentFile(data), save=False)
                except Exception:
                    pass

            servico.save()
            messages.success(request, "Serviço criado com sucesso!")
            return redirect("agendamentos:gerir_servicos")
        messages.error(request, "Erro ao criar serviço. Verifique os dados.")
    else:
        form = ServicoForm()

    return render(request, "agendamentos/criar_editar_servico.html", {"form": form, "servico": None})


@login_required
def editar_servico(request, servico_id: int):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para editar serviços.")
        return redirect("agendamentos:painel")

    servico = get_object_or_404(Servico, id=servico_id)

    if request.method == "POST":
        form = ServicoForm(request.POST, request.FILES, instance=servico)
        if form.is_valid():
            servico = form.save(commit=False)

            imagem_base64 = request.POST.get("imagem_base64")
            if imagem_base64:
                try:
                    header, data64 = imagem_base64.split(";base64,")
                    ext = header.split("/")[-1]
                    data = base64.b64decode(data64)
                    from django.core.files.base import ContentFile
                    servico.imagem.save(f"servico_{servico.nome}.{ext}", ContentFile(data), save=False)
                except Exception:
                    pass

            servico.save()
            messages.success(request, "Serviço atualizado com sucesso!")
            return redirect("agendamentos:gerir_servicos")
        messages.error(request, "Erro ao atualizar serviço. Verifique os dados.")
    else:
        form = ServicoForm(instance=servico)

    return render(request, "agendamentos/criar_editar_servico.html", {"form": form, "servico": servico})


@login_required
def excluir_servico(request, servico_id: int):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para excluir serviços.")
        return redirect("agendamentos:painel")

    servico = get_object_or_404(Servico, id=servico_id)
    if request.method == "POST":
        servico.delete()
        messages.success(request, "Serviço excluído com sucesso!")
        return redirect("agendamentos:gerir_servicos")

    return render(request, "agendamentos/excluir_servico_confirm.html", {"servico": servico})


@login_required
def remover_imagem_servico(request, servico_id: int):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para remover imagens.")
        return redirect("agendamentos:painel")

    servico = get_object_or_404(Servico, id=servico_id)
    if request.method == "POST":
        if servico.imagem:
            servico.imagem.delete(save=False)
            servico.save()
            messages.success(request, "Imagem principal removida com sucesso!")
        else:
            messages.info(request, "Nenhuma imagem principal para remover.")
    return redirect("agendamentos:editar_servico", servico_id=servico.id)


@login_required
def recortar_imagem_servico(request, servico_id: int):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para recortar imagens.")
        return redirect("agendamentos:painel")

    servico = get_object_or_404(Servico, id=servico_id)

    if request.method == "POST":
        cropped = request.POST.get("cropped_image_data")
        if not cropped:
            messages.error(request, "Dados da imagem recortada não recebidos.")
            return redirect("agendamentos:editar_servico", servico_id=servico.id)
        try:
            header, data64 = cropped.split(";base64,")
            ext = header.split("/")[-1]
            data = base64.b64decode(data64)
            from django.core.files.base import ContentFile
            servico.imagem.save(f"servico_{servico.nome}_crop.{ext}", ContentFile(data), save=True)
            messages.success(request, "Imagem recortada e salva com sucesso!")
        except Exception as e:
            messages.error(request, f"Erro ao recortar/salvar imagem: {e}")
        return redirect("agendamentos:editar_servico", servico_id=servico.id)

    return render(request, "agendamentos/recortar_imagem_servico.html", {"servico": servico})


# ============================================================
# IMAGENS ADICIONAIS (opcional)
# ============================================================

@login_required
def adicionar_imagens_adicionais(request, servico_id: int):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para adicionar imagens.")
        return redirect("agendamentos:painel")

    if ServicoImagem is None:
        messages.error(request, "O recurso de imagens adicionais não está disponível (modelo ausente).")
        return redirect("agendamentos:editar_servico", servico_id=servico_id)

    servico = get_object_or_404(Servico, id=servico_id)
    if request.method == "POST":
        imagens = request.FILES.getlist("imagens_adicionais")
        if not imagens:
            messages.error(request, "Nenhuma imagem selecionada para upload.")
            return redirect("agendamentos:editar_servico", servico_id=servico.id)

        existentes = ServicoImagem.objects.filter(servico=servico).count()
        disponiveis = max(0, 5 - existentes)
        for f in imagens[:disponiveis]:
            ServicoImagem.objects.create(servico=servico, imagem=f)
        if len(imagens) > disponiveis:
            messages.warning(request, "Limite de 5 imagens adicionais por serviço.")
        else:
            messages.success(request, f"{min(len(imagens), disponiveis)} imagens adicionadas ao serviço {servico.nome}!")
    return redirect("agendamentos:editar_servico", servico_id=servico.id)


@login_required
def remover_imagem_adicional(request, imagem_id: int):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para remover imagens.")
        return redirect("agendamentos:painel")

    if ServicoImagem is None:
        messages.error(request, "O recurso de imagens adicionais não está disponível (modelo ausente).")
        return redirect("agendamentos:painel")

    img = get_object_or_404(ServicoImagem, id=imagem_id)
    servico_id = img.servico.id
    if request.method == "POST":
        img.imagem.delete(save=False)
        img.delete()
        messages.success(request, "Imagem adicional removida com sucesso!")
    return redirect("agendamentos:editar_servico", servico_id=servico_id)


# ============================================================
# RESULTADOS (painel - staff)
# ============================================================

@login_required
def gerir_resultados(request):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("agendamentos:painel")
    resultados = ResultadoAluna.objects.all().order_by("ordem", "-criado_em")
    return render(request, "agendamentos/gerir_resultados.html", {"resultados": resultados})


@login_required
def criar_resultado(request):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para criar.")
        return redirect("agendamentos:painel")
    if request.method == "POST":
        nome = request.POST.get("nome_aluna", "").strip()
        tecnica = request.POST.get("tecnica", "").strip()
        ativo = request.POST.get("ativo") == "on"
        foto = request.FILES.get("foto")
        ordem = int(request.POST.get("ordem") or 0)
        if not (nome and tecnica and foto):
            messages.error(request, "Preencha nome, técnica e selecione a foto.")
        else:
            ResultadoAluna.objects.create(
                nome_aluna=nome, tecnica=tecnica, foto=foto, ativo=ativo, ordem=ordem
            )
            messages.success(request, "Resultado criado!")
            return redirect("agendamentos:gerir_resultados")
    return render(request, "agendamentos/criar_editar_resultado.html", {"titulo": "Novo Resultado", "obj": None})


@login_required
def editar_resultado(request, resultado_id: int):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para editar.")
        return redirect("agendamentos:painel")
    obj = get_object_or_404(ResultadoAluna, id=resultado_id)
    if request.method == "POST":
        obj.nome_aluna = request.POST.get("nome_aluna", "").strip()
        obj.tecnica = request.POST.get("tecnica", "").strip()
        obj.ativo = request.POST.get("ativo") == "on"
        obj.ordem = int(request.POST.get("ordem") or 0)
        if request.FILES.get("foto"):
            obj.foto = request.FILES["foto"]
        obj.save()
        messages.success(request, "Resultado atualizado!")
        return redirect("agendamentos:gerir_resultados")
    return render(request, "agendamentos/criar_editar_resultado.html", {"titulo": "Editar Resultado", "obj": obj})


@login_required
def excluir_resultado(request, resultado_id: int):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para excluir.")
        return redirect("agendamentos:painel")
    obj = get_object_or_404(ResultadoAluna, id=resultado_id)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Resultado excluído!")
        return redirect("agendamentos:gerir_resultados")
    return render(request, "agendamentos/excluir_resultado_confirm.html", {"obj": obj})


# ============================================================
# PROVA SOCIAL (painel - staff) — SEPARADO
# ============================================================

@login_required
def gerir_provas(request):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("agendamentos:painel")
    provas = ProvaSocial.objects.all().order_by("ordem", "-criado_em")
    return render(request, "agendamentos/gerir_provas.html", {"provas": provas})


@login_required
def criar_prova(request):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para criar.")
        return redirect("agendamentos:painel")
    if request.method == "POST":
        legenda = request.POST.get("legenda", "").strip()
        ativo = request.POST.get("ativo") == "on"
        ordem = int(request.POST.get("ordem") or 0)
        imagem = request.FILES.get("imagem")
        if not imagem:
            messages.error(request, "Selecione a imagem (print do feedback).")
        else:
            ProvaSocial.objects.create(imagem=imagem, legenda=legenda, ativo=ativo, ordem=ordem)
            messages.success(request, "Prova social criada!")
            return redirect("agendamentos:gerir_provas")
    return render(request, "agendamentos/criar_editar_prova.html", {"titulo": "Nova Prova Social", "obj": None})


@login_required
def editar_prova(request, prova_id: int):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para editar.")
        return redirect("agendamentos:painel")
    obj = get_object_or_404(ProvaSocial, id=prova_id)
    if request.method == "POST":
        obj.legenda = request.POST.get("legenda", "").strip()
        obj.ativo = request.POST.get("ativo") == "on"
        obj.ordem = int(request.POST.get("ordem") or 0)
        if request.FILES.get("imagem"):
            obj.imagem = request.FILES["imagem"]
        obj.save()
        messages.success(request, "Prova social atualizada!")
        return redirect("agendamentos:gerir_provas")
    return render(request, "agendamentos/criar_editar_prova.html", {"titulo": "Editar Prova Social", "obj": obj})


@login_required
def excluir_prova(request, prova_id: int):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para excluir.")
        return redirect("agendamentos:painel")
    obj = get_object_or_404(ProvaSocial, id=prova_id)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Prova social excluída!")
        return redirect("agendamentos:gerir_provas")
    return render(request, "agendamentos/excluir_prova_confirm.html", {"obj": obj})
