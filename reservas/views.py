from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from faturacao.models import Pagamento
from reservas.disponibilidade import unidade_disponivel_no_periodo
from reservas.forms_public import EditarReservaForm
from reservas.referencia_pagamento import formatar_instrucoes_pagamento
from reservas.models import Reserva
from usuarios.authz import cliente_required, interno_required


@interno_required
def lista(request):
    if request.method == "POST":
        reserva = get_object_or_404(Reserva.objects.select_related("cliente"), pk=request.POST.get("reserva_id"))
        acao = request.POST.get("acao")
        if acao == "confirmar":
            reserva.status = "confirmada"
            reserva.save(update_fields=["status"])
            messages.success(request, f"Reserva #{reserva.id} confirmada.")
        elif acao == "cancelar":
            reserva.status = "cancelada"
            reserva.save(update_fields=["status"])
            if reserva.cliente.estado != "inativo":
                reserva.cliente.estado = "inativo"
                reserva.cliente.save(update_fields=["estado"])
            messages.warning(request, f"Reserva #{reserva.id} cancelada.")
        elif acao == "whatsapp_sim":
            reserva.pagamento_confirmado_whatsapp = True
            reserva.save(update_fields=["pagamento_confirmado_whatsapp", "status"])
            messages.success(request, f"Pagamento da reserva #{reserva.id} confirmado por WhatsApp.")
        return redirect("reservas:lista")

    reservas = Reserva.objects.select_related("cliente", "unidade", "epoca").order_by("-id")[:100]
    return render(request, "reservas/lista.html", {"reservas": reservas})


def _status_pagamento(reserva: Reserva) -> str:
    pg = Pagamento.objects.filter(fatura__reserva=reserva).order_by("-id").first()
    return pg.status if pg else "pendente"


def _garantir_snapshot_reserva(reserva: Reserva) -> Reserva:
    """
    Garante que a página de resumo nunca apareça vazia:
    se algum campo de snapshot estiver em branco, preenche a partir do perfil Cliente.
    """
    cliente = reserva.cliente
    alterou = False
    mapeamento = {
        "nome_completo": cliente.nome or "",
        "telefone": cliente.telefone or "",
        "email": cliente.email or "",
        "nacionalidade": cliente.nacionalidade or "",
        "tipo_documento": cliente.tipo_documento or "",
        "numero_documento_identificacao": cliente.numero_documento_identificacao or "",
        "morada": cliente.morada or "",
        "cidade": cliente.cidade or "",
        "pais_residencia": cliente.pais_residencia or "",
        "contacto_alternativo": cliente.contacto_alternativo or "",
        "preferencia_contacto": cliente.preferencia_contacto or "",
    }
    for campo, valor in mapeamento.items():
        atual = getattr(reserva, campo)
        if not atual and valor:
            setattr(reserva, campo, valor)
            alterou = True
    if reserva.data_nascimento is None and cliente.data_nascimento is not None:
        reserva.data_nascimento = cliente.data_nascimento
        alterou = True
    if alterou:
        reserva.save()
    return reserva


@cliente_required
def minhas_reservas(request):
    reservas = (
        Reserva.objects.filter(cliente__user=request.user)
        .select_related("unidade", "cliente")
        .order_by("-id")
    )
    dados = [{"reserva": r, "status_pagamento": _status_pagamento(r)} for r in reservas]
    return render(request, "reservas/minhas_reservas.html", {"dados": dados})


@cliente_required
def detalhe_reserva(request, reserva_id: int):
    reserva = get_object_or_404(
        Reserva.objects.select_related("unidade", "cliente"),
        pk=reserva_id,
        cliente__user=request.user,
    )
    reserva = _garantir_snapshot_reserva(reserva)
    pagamentos = Pagamento.objects.filter(fatura__reserva=reserva).order_by("-id")
    return render(
        request,
        "reservas/detalhe_reserva.html",
        {
            "reserva": reserva,
            "pagamentos": pagamentos,
            "instrucoes_pagamento": formatar_instrucoes_pagamento(reserva),
            "whatsapp_rececao": getattr(settings, "RECECAO_WHATSAPP_MSISDN", ""),
        },
    )


@cliente_required
def resumo_pagamento(request, reserva_id: int):
    reserva = get_object_or_404(
        Reserva.objects.select_related("unidade", "cliente"),
        pk=reserva_id,
        cliente__user=request.user,
    )
    reserva = _garantir_snapshot_reserva(reserva)
    pagamento = Pagamento.objects.filter(fatura__reserva=reserva).order_by("-id").first()
    return render(
        request,
        "reservas/resumo_pagamento.html",
        {
            "reserva": reserva,
            "pagamento": pagamento,
            "instrucoes_pagamento": formatar_instrucoes_pagamento(reserva),
            "whatsapp_rececao": getattr(settings, "RECECAO_WHATSAPP_MSISDN", ""),
        },
    )


@cliente_required
def editar_reserva(request, reserva_id: int):
    reserva = get_object_or_404(
        Reserva.objects.select_related("cliente", "unidade"),
        pk=reserva_id,
        cliente__user=request.user,
    )
    if reserva.status not in {"aguardando_pagamento", "pagamento_em_validacao", "pre_reserva"}:
        messages.warning(request, "A edição só está disponível para reservas ainda não confirmadas.")
        return redirect("reservas:detalhe_reserva", reserva_id=reserva.pk)

    if request.method == "POST":
        form = EditarReservaForm(request.POST)
        if form.is_valid():
            di = form.cleaned_data["data_checkin"]
            df = form.cleaned_data["data_checkout"]
            if not unidade_disponivel_no_periodo(reserva.unidade_id, di, df):
                form.add_error(None, "Esta unidade ficou indisponível para as datas escolhidas.")
            else:
                dados = form.cleaned_data
                for campo_modelo, campo_form in (
                    ("nome_completo", "nome_completo"),
                    ("telefone", "telefone"),
                    ("email", "email"),
                    ("nacionalidade", "nacionalidade"),
                    ("tipo_documento", "tipo_documento"),
                    ("numero_documento_identificacao", "numero_documento_identificacao"),
                    ("data_nascimento", "data_nascimento"),
                    ("morada", "morada"),
                    ("cidade", "cidade"),
                    ("pais_residencia", "pais_residencia"),
                    ("contacto_alternativo", "contacto_alternativo"),
                    ("preferencia_contacto", "preferencia_contacto"),
                    ("data_inicio", "data_checkin"),
                    ("data_fim", "data_checkout"),
                    ("numero_hospedes", "numero_hospedes"),
                    ("finalidade_estadia", "finalidade_estadia"),
                    ("observacoes", "observacoes"),
                    ("pedido_especial", "pedido_especial"),
                ):
                    valor = dados.get(campo_form)
                    if valor is None and campo_modelo in {"data_nascimento"}:
                        setattr(reserva, campo_modelo, None)
                    elif valor is None:
                        setattr(reserva, campo_modelo, "")
                    else:
                        setattr(reserva, campo_modelo, valor)
                reserva.save()
                cliente = reserva.cliente
                cliente.nome = dados["nome_completo"]
                cliente.telefone = dados["telefone"]
                cliente.email = dados["email"]
                cliente.nacionalidade = dados["nacionalidade"]
                cliente.tipo_documento = dados["tipo_documento"]
                cliente.numero_documento_identificacao = dados["numero_documento_identificacao"]
                cliente.data_nascimento = dados.get("data_nascimento")
                cliente.morada = dados.get("morada") or ""
                cliente.cidade = dados.get("cidade") or ""
                cliente.pais_residencia = dados.get("pais_residencia") or ""
                cliente.contacto_alternativo = dados.get("contacto_alternativo") or ""
                cliente.preferencia_contacto = dados.get("preferencia_contacto") or ""
                cliente.save()
                messages.success(request, "Dados da reserva atualizados com sucesso.")
                return redirect("reservas:resumo_pagamento", reserva_id=reserva.pk)
    else:
        form = EditarReservaForm(
            initial={
                "nome_completo": reserva.nome_completo,
                "telefone": reserva.telefone,
                "email": reserva.email,
                "nacionalidade": reserva.nacionalidade,
                "tipo_documento": reserva.tipo_documento,
                "numero_documento_identificacao": reserva.numero_documento_identificacao,
                "data_nascimento": reserva.data_nascimento,
                "morada": reserva.morada,
                "cidade": reserva.cidade,
                "pais_residencia": reserva.pais_residencia,
                "contacto_alternativo": reserva.contacto_alternativo,
                "preferencia_contacto": reserva.preferencia_contacto,
                "data_checkin": reserva.data_inicio,
                "data_checkout": reserva.data_fim,
                "numero_hospedes": reserva.numero_hospedes,
                "finalidade_estadia": reserva.finalidade_estadia,
                "observacoes": reserva.observacoes,
                "pedido_especial": reserva.pedido_especial,
            }
        )

    return render(request, "reservas/editar_reserva.html", {"reserva": reserva, "form": form})
