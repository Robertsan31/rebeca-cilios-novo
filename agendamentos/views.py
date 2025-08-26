# agendamentos/views.py
from __future__ import annotations

import base64
import csv
import io
import json
import re
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

# >>> IMPORTS para stats <<<
from django.db.models import Count, Q
from django.db.models.functions import TruncDate

from .forms import ClienteForm, ServicoForm
from .models import Cliente, Servico, Agendamento


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _salvar_base64_no_servico(servico: Servico, data_url: str) -> None:
    """
    Recebe um dataURL (base64) e grava em servico.imagem dentro de 'servicos/' já normalizado
    para JPEG RGB 1200x1200. Fallback: salva bruto conforme MIME.
    """
    from io import BytesIO

    try:
        from PIL import Image  # type: ignore
        PIL_OK = True
    except Exception:
        PIL_OK = False

    m = re.match(r"^data:(image\/[A-Za-z0-9.+-]+);base64,(.+)$", data_url)
    if not m:
        raise ValueError("dataURL inválido.")
    mime = m.group(1).lower()
    raw = base64.b64decode(m.group(2))
    stamp = timezone.now().strftime("%Y%m%d_%H%M%S")

    if PIL_OK:
        bio = BytesIO(raw)
        img = Image.open(bio)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        elif img.mode == "L":
            img = img.convert("RGB")
        w, h = img.size
        if w != h:
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            img = img.crop((left, top, left + side, top + side))
        img = img.resize((1200, 1200), Image.Resampling.LANCZOS)
        out = BytesIO()
        img.save(out, format="JPEG", quality=90, optimize=True)
        out.seek(0)
        filename = f"servicos/servico_{servico.id}_{stamp}.jpg"
        if servico.imagem:
            try:
                servico.imagem.delete(save=False)
            except Exception:
                pass
        servico.imagem.save(filename, ContentFile(out.read()), save=True)
    else:
        ext = "jpg"
        if "png" in mime:
            ext = "png"
        elif "webp" in mime:
            ext = "webp"
        filename = f"servicos/servico_{servico.id}_{stamp}.{ext}"
        if servico.imagem:
            try:
                servico.imagem.delete(save=False)
            except Exception:
                pass
        servico.imagem.save(filename, ContentFile(raw), save=True)


# -----------------------------------------------------------------------------
# PÚBLICO
# -----------------------------------------------------------------------------
def home(request: HttpRequest) -> HttpResponse:
    return render(request, "agendamentos/home.html")


def lista_servicos(request: HttpRequest) -> HttpResponse:
    servicos = list(Servico.objects.all().order_by("id"))
    for s in servicos:
        if getattr(s, "imagem", None):
            try:
                if not default_storage.exists(s.imagem.name):
                    s.imagem = None
            except Exception:
                s.imagem = None
    return render(request, "agendamentos/lista_servicos.html", {"servicos": servicos})


# -----------------------------------------------------------------------------
# PAINEL / DASHBOARD
# -----------------------------------------------------------------------------
@login_required
def painel(request: HttpRequest) -> HttpResponse:
    servicos = list(Servico.objects.values("id", "nome", "preco").order_by("id"))
    servicos_json = json.dumps(servicos, ensure_ascii=False, cls=DjangoJSONEncoder)
    return render(request, "agendamentos/painel.html", {"servicos_json": servicos_json})


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "agendamentos/dashboard.html")


@login_required
def dashboard_export_csv(request: HttpRequest) -> HttpResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Relatório", timezone.now().strftime("%Y-%m-%d %H:%M")])
    writer.writerow([])
    writer.writerow(["Serviço", "Preço"])
    for s in Servico.objects.all().order_by("id"):
        writer.writerow([s.nome, s.preco])

    resp = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="dashboard.csv"'
    return resp


@login_required
def dashboard_export_pdf(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Export PDF não implementado aqui.", content_type="text/plain")


# -----------------------------------------------------------------------------
# ESTATÍSTICAS (implementado)
# -----------------------------------------------------------------------------
@require_GET
@login_required
def stats(request: HttpRequest) -> JsonResponse:
    """
    Retorna séries agregadas por dia dentro da janela solicitada (days=7/30/90...).
    Shape do JSON compatível com o dashboard.html.
    """
    days = int(request.GET.get("days", 30))
    if days < 1:
        days = 7

    tz = timezone.get_current_timezone()
    hoje_local = timezone.localdate()
    inicio = hoje_local - timedelta(days=days - 1)

    # Agregação por dia e por status (1 query)
    agregados = (
        Agendamento.objects
        .filter(data_hora__date__gte=inicio, data_hora__date__lte=hoje_local)
        .annotate(dia=TruncDate("data_hora", tzinfo=tz))
        .values("dia")
        .annotate(
            total=Count("id"),
            confirmado=Count("id", filter=Q(status="Confirmado")),
            realizado=Count("id", filter=Q(status="Realizado")),
            cancelado=Count("id", filter=Q(status="Cancelado")),
            pendente=Count("id", filter=Q(status="Pendente")),
        )
        .order_by("dia")
    )

    por_dia = {row["dia"]: row for row in agregados}

    labels = []
    serie_total, serie_conf, serie_real, serie_canc, serie_pend = [], [], [], [], []
    for i in range(days):
        d = inicio + timedelta(days=i)
        labels.append(d.strftime("%d/%m"))
        row = por_dia.get(d)
        if row:
            serie_total.append(row["total"])
            serie_conf.append(row["confirmado"])
            serie_real.append(row["realizado"])
            serie_canc.append(row["cancelado"])
            serie_pend.append(row["pendente"])
        else:
            serie_total.append(0)
            serie_conf.append(0)
            serie_real.append(0)
            serie_canc.append(0)
            serie_pend.append(0)

    return JsonResponse({
        "labels": labels,
        "series": {
            "total": serie_total,
            "confirmado": serie_conf,
            "realizado": serie_real,
            "cancelado": serie_canc,
            "pendente": serie_pend,
        },
    })


# -----------------------------------------------------------------------------
# API do calendário
# -----------------------------------------------------------------------------
@require_GET
@login_required
def api_agendamentos(request: HttpRequest) -> JsonResponse:
    """
    Retorna eventos pro FullCalendar (com cores por status).
    Faz parsing de start/end em ISO se vierem presentes.
    """
    start = request.GET.get("start")
    end = request.GET.get("end")

    qs = Agendamento.objects.select_related("cliente", "servico")

    # (opcional) interpretar ISO-8601
    if start:
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            qs = qs.filter(data_hora__gte=start_dt)
        except ValueError:
            pass
    if end:
        try:
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            qs = qs.filter(data_hora__lte=end_dt)
        except ValueError:
            pass

    eventos = []
    for a in qs:
        # cor por status
        bg = "#6c757d"  # default
        if a.status == "Confirmado":
            bg = "#198754"
        elif a.status == "Cancelado":
            bg = "#dc3545"
        elif a.status == "Pendente":
            bg = "#ffc107"
        elif a.status == "Realizado":
            bg = "#0dcaf0"

        eventos.append(
            {
                "id": a.id,
                "title": f"{a.data_hora.strftime('%H:%M')} {a.servico.nome if a.servico else ''}",
                "start": a.data_hora.isoformat(),
                "allDay": False,
                "backgroundColor": bg,
                "borderColor": bg,
                "textColor": "#FFFFFF",
                "extendedProps": {
                    "status": a.status,
                    "cliente_nome": a.cliente.nome if a.cliente else "",
                    "cliente_email": a.cliente.email if a.cliente else "",
                    "cliente_telefone": a.cliente.telefone if a.cliente else "",
                    "servico_nome": a.servico.nome if a.servico else "",
                },
            }
        )

    return JsonResponse(eventos, safe=False)


@require_GET
@login_required
def api_notificacao_proximo_agendamento(request: HttpRequest) -> JsonResponse:
    """
    Exemplo simples: retorna se há próximo agendamento nas próximas 24h.
    (Você pode enriquecer depois para reativar o lembrete WhatsApp.)
    """
    agora = timezone.now()
    proximo = (
        Agendamento.objects.filter(data_hora__gte=agora, status__in=["Pendente", "Confirmado"])
        .order_by("data_hora")
        .first()
    )
    return JsonResponse({"has_next": bool(proximo)})


# -----------------------------------------------------------------------------
# FLUXO DE AGENDAMENTO (básico)
# -----------------------------------------------------------------------------
@login_required
def agendar_servico(request: HttpRequest, servico_id: int) -> HttpResponse:
    servico = get_object_or_404(Servico, id=servico_id)

    # valida data (querystring ?data=YYYY-MM-DD) e não permitir passado
    data_str = request.GET.get("data")
    dia = timezone.localdate()
    if data_str:
        try:
            dia = datetime.strptime(data_str, "%Y-%m-%d").date()
        except Exception:
            pass

    if request.method == "POST":
        hora = request.POST.get("hora")  # ex: "13:30"
        if not hora:
            return render(
                request,
                "agendamentos/agendar_servico.html",
                {"servico": servico, "error_message": "Informe um horário.", "dia": dia},
            )

        try:
            hh, mm = map(int, hora.split(":"))
            data_hora = timezone.make_aware(datetime(dia.year, dia.month, dia.day, hh, mm))
        except Exception:
            return render(
                request,
                "agendamentos/agendar_servico.html",
                {"servico": servico, "error_message": "Horário inválido.", "dia": dia},
            )

        # bloqueia passado
        if data_hora < timezone.now():
            return render(
                request,
                "agendamentos/agendar_servico.html",
                {
                    "servico": servico,
                    "error_message": "Não é possível agendar no passado.",
                    "dia": dia,
                },
            )

        # redireciona para confirmar (simplificado)
        return redirect(
            "agendamentos:confirmar_agendamento",
            servico_id=servico.id,
            year=data_hora.year,
            month=data_hora.month,
            day=data_hora.day,
            hour=data_hora.hour,
            minute=data_hora.minute,
        )

    return render(request, "agendamentos/agendar_servico.html", {"servico": servico, "dia": dia})


@login_required
def confirmar_agendamento(
    request: HttpRequest, servico_id: int, year: int, month: int, day: int, hour: int, minute: int
) -> HttpResponse:
    servico = get_object_or_404(Servico, id=servico_id)
    data_hora = timezone.make_aware(datetime(year, month, day, hour, minute))

    # bloqueia passado
    if data_hora < timezone.now():
        return render(
            request,
            "agendamentos/confirmar_agendamento.html",
            {"servico": servico, "data_hora": data_hora, "error_message": "Não é possível agendar no passado."},
        )

    clientes = Cliente.objects.all().order_by("nome")

    if request.method == "POST":
        origem = request.POST.get("cliente_origem", "existente")
        if origem == "existente":
            cid = request.POST.get("cliente_id")
            if not cid:
                return render(
                    request,
                    "agendamentos/confirmar_agendamento.html",
                    {"servico": servico, "data_hora": data_hora, "clientes": clientes, "error_message": "Selecione a cliente."},
                )
            cliente = get_object_or_404(Cliente, id=int(cid))
        else:
            form = ClienteForm(request.POST)
            if not form.is_valid():
                return render(
                    request,
                    "agendamentos/confirmar_agendamento.html",
                    {"servico": servico, "data_hora": data_hora, "clientes": clientes, "form": form},
                )
            cliente = form.save()

        Agendamento.objects.create(
            cliente=cliente,
            servico=servico,
            data_hora=data_hora,
            status="Confirmado",
        )
        messages.success(request, "Agendamento criado com sucesso!")
        return redirect("agendamentos:painel")

    form = ClienteForm()
    return render(
        request,
        "agendamentos/confirmar_agendamento.html",
        {"servico": servico, "data_hora": data_hora, "clientes": clientes, "form": form},
    )


# -----------------------------------------------------------------------------
# GERENCIAMENTO DE AGENDAMENTOS
# -----------------------------------------------------------------------------
@login_required
def gerir_agendamentos(request: HttpRequest) -> HttpResponse:
    data_str = request.GET.get("data")
    dia = timezone.localdate()
    if data_str:
        try:
            dia = datetime.strptime(data_str, "%Y-%m-%d").date()
        except Exception:
            pass

    inicio = timezone.make_aware(datetime(dia.year, dia.month, dia.day, 0, 0))
    fim = inicio + timedelta(days=1)
    agendamentos = (
        Agendamento.objects.select_related("cliente", "servico")
        .filter(data_hora__gte=inicio, data_hora__lt=fim)
        .order_by("data_hora")
    )

    return render(
        request,
        "agendamentos/gerir_agendamentos.html",
        {"agendamentos": agendamentos, "dia_selecionado": dia, "data": dia},
    )


@login_required
@require_http_methods(["POST"])
def atualizar_status_agendamento(request: HttpRequest, agendamento_id: int):
    ag = get_object_or_404(Agendamento, id=agendamento_id)

    novo_status = request.POST.get("status")
    status_validos = dict(Agendamento.STATUS_CHOICES)
    if novo_status not in status_validos:
        if request.headers.get("x-requested-with") == "XMLHttpRequest" or "application/json" in (request.headers.get("Accept") or ""):
            return JsonResponse({"ok": False, "error": "Status inválido."}, status=400)
        messages.error(request, "Status inválido.")
        return redirect(reverse("agendamentos:gerir_agendamentos") + f"?data={ag.data_hora.date().isoformat()}")

    ag.status = novo_status
    ag.save(update_fields=["status"])
    messages.success(request, f"Agendamento atualizado para: {novo_status}.")

    if request.headers.get("x-requested-with") == "XMLHttpRequest" or "application/json" in (request.headers.get("Accept") or ""):
        return JsonResponse({"ok": True, "status": ag.status})

    next_url = (
        request.POST.get("next")
        or request.META.get("HTTP_REFERER")
        or reverse("agendamentos:gerir_agendamentos")
    )
    base = reverse("agendamentos:gerir_agendamentos")
    if base in next_url:
        next_url = base + f"?data={ag.data_hora.date().isoformat()}"
    return redirect(next_url)


# -----------------------------------------------------------------------------
# CRUD DE SERVIÇOS (com recorte de imagem)
# -----------------------------------------------------------------------------
@login_required
def gerir_servicos(request: HttpRequest) -> HttpResponse:
    servicos = list(Servico.objects.all().order_by("id"))
    for s in servicos:
        if getattr(s, "imagem", None):
            try:
                if not default_storage.exists(s.imagem.name):
                    s.imagem = None
            except Exception:
                s.imagem = None
    return render(request, "agendamentos/gerir_servicos.html", {"servicos": servicos})


@login_required
def criar_servico(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ServicoForm(request.POST, request.FILES)
        if form.is_valid():
            servico = form.save()
            crop_data = request.POST.get("cropped_image_data", "")
            if crop_data:
                _salvar_base64_no_servico(servico, crop_data)
                messages.success(request, "Serviço criado e imagem recortada com sucesso!")
                return redirect("agendamentos:gerir_servicos")
            if request.FILES.get("imagem"):
                messages.success(request, "Serviço criado! Agora recorte a imagem.")
                return redirect("agendamentos:recortar_imagem_servico", servico.id)
            messages.success(request, "Serviço criado com sucesso!")
            return redirect("agendamentos:gerir_servicos")
    else:
        form = ServicoForm()

    return render(
        request,
        "agendamentos/criar_editar_servico.html",
        {"form": form, "titulo_pagina": "Novo Serviço"},
    )


@login_required
def editar_servico(request: HttpRequest, servico_id: int) -> HttpResponse:
    servico = get_object_or_404(Servico, id=servico_id)

    if request.method == "POST":
        form = ServicoForm(request.POST, request.FILES, instance=servico)
        if form.is_valid():
            servico = form.save()
            crop_data = request.POST.get("cropped_image_data", "")
            if crop_data:
                _salvar_base64_no_servico(servico, crop_data)
                messages.success(request, "Serviço atualizado e imagem recortada com sucesso!")
                return redirect("agendamentos:gerir_servicos")
            if request.FILES.get("imagem"):
                messages.success(request, "Serviço atualizado! Agora recorte a nova imagem.")
                return redirect("agendamentos:recortar_imagem_servico", servico.id)
            messages.success(request, "Serviço atualizado com sucesso!")
            return redirect("agendamentos:gerir_servicos")
    else:
        form = ServicoForm(instance=servico)

    return render(
        request,
        "agendamentos/criar_editar_servico.html",
        {"form": form, "titulo_pagina": "Editar Serviço"},
    )


@login_required
@require_http_methods(["POST"])
def excluir_servico(request: HttpRequest, servico_id: int) -> HttpResponse:
    servico = get_object_or_404(Servico, id=servico_id)
    servico.delete()
    messages.success(request, "Serviço excluído.")
    return redirect("agendamentos:gerir_servicos")


@login_required
@require_http_methods(["POST"])
def remover_imagem_servico(request: HttpRequest, servico_id: int) -> HttpResponse:
    servico = get_object_or_404(Servico, id=servico_id)
    if servico.imagem:
        try:
            servico.imagem.delete(save=False)
        except Exception:
            pass
        servico.imagem = None
        servico.save(update_fields=["imagem"])
    messages.success(request, "Imagem removida.")
    return redirect("agendamentos:editar_servico", servico_id=servico.id)


@login_required
@require_http_methods(["GET", "POST"])
def recortar_imagem_servico(request: HttpRequest, servico_id: int) -> HttpResponse:
    servico = get_object_or_404(Servico, id=servico_id)

    if request.method == "POST":
        data_url = request.POST.get("cropData", "")
        if not data_url:
            messages.error(request, "Nenhum recorte foi enviado.")
            return redirect("agendamentos:recortar_imagem_servico", servico.id)
        try:
            _salvar_base64_no_servico(servico, data_url)
        except Exception:
            messages.error(request, "Não foi possível processar a imagem.")
            return redirect("agendamentos:recortar_imagem_servico", servico.id)

        messages.success(request, "Imagem atualizada com sucesso!")
        return redirect("agendamentos:gerir_servicos")

    imagem_url = servico.imagem.url if servico.imagem else ""
    return render(
        request,
        "agendamentos/recortar_imagem_servico.html",
        {"servico": servico, "imagem_url": imagem_url},
    )


# -----------------------------------------------------------------------------
# CRUD DE CLIENTES
# -----------------------------------------------------------------------------
@login_required
def gerir_clientes(request: HttpRequest) -> HttpResponse:
    clientes = Cliente.objects.all().order_by("id")
    return render(request, "agendamentos/gerir_clientes.html", {"clientes": clientes})


@login_required
def editar_cliente(request: HttpRequest, cliente_id: int) -> HttpResponse:
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente atualizado.")
            return redirect("agendamentos:gerir_clientes")
    else:
        form = ClienteForm(instance=cliente)
    return render(request, "agendamentos/editar_cliente.html", {"form": form})


@login_required
@require_http_methods(["POST"])
def excluir_cliente(request: HttpRequest, cliente_id: int) -> HttpResponse:
    cliente = get_object_or_404(Cliente, id=cliente_id)
    cliente.delete()
    messages.success(request, "Cliente excluído.")
    return redirect("agendamentos:gerir_clientes")
