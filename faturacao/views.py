from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from faturacao.models import Fatura
from faturacao.notificacoes import enviar_fatura_por_email_apos_pagamento
from faturacao.services import (
    add_item_fatura,
    gerar_fatura_automatica_reserva,
    gerar_fatura_servicos_reserva,
    recalcular_total_fatura,
)
from reservas.models import Reserva
from usuarios.authz import interno_required
from usuarios.roles import PERFIL_ADMINISTRADOR, get_user_profile

from .forms import FaturaForm, ItemManualForm


def _resumo_reserva_faturacao(reserva):
    limpeza = list(reserva.pedidos_limpeza.exclude(status="cancelado"))
    lav = list(reserva.pedidos_lavandaria.exclude(status="cancelado"))
    rest = list(reserva.pedidos_restaurante.exclude(status="cancelado"))
    total_servicos = sum((p.preco for p in limpeza), start=0) + sum((p.preco_total for p in lav), start=0) + sum(
        (p.total for p in rest), start=0
    )
    return {
        "reserva": reserva,
        "cliente_nome": reserva.cliente.nome,
        "telefone": reserva.cliente.telefone,
        "email": reserva.cliente.email,
        "documento": reserva.cliente.numero_documento_identificacao,
        "apartamento": reserva.unidade.codigo,
        "tipologia": reserva.unidade.tipo,
        "periodo": f"{reserva.data_inicio} a {reserva.data_fim}",
        "estado_reserva": reserva.status,
        "estado_pagamento": "pago" if reserva.cliente.situacao_financeira == "paga" else "pendente",
        "servicos_pendentes": len(limpeza) + len(lav) + len(rest),
        "total_servicos": total_servicos,
        "total_faturar": reserva.valor_base + total_servicos,
    }


@interno_required
def lista(request):
    status = (request.GET.get("status") or "").strip()
    faturas = Fatura.objects.select_related("reserva", "reserva__cliente", "cliente").order_by("-id")
    if status in {"emitida", "paga", "cancelada"}:
        faturas = faturas.filter(status=status)
    totais = {
        "emitida": Fatura.objects.filter(status="emitida").count(),
        "paga": Fatura.objects.filter(status="paga").count(),
        "cancelada": Fatura.objects.filter(status="cancelada").count(),
    }
    return render(
        request,
        "faturacao/lista.html",
        {"faturas": faturas[:100], "status": status, "totais": totais},
    )


@interno_required
def emitir_fatura(request):
    item_forms = [ItemManualForm(prefix=f"item{i}") for i in range(1, 4)]
    form = FaturaForm(request.POST or None)
    query = (request.GET.get("q") or "").strip()
    reserva_id = request.GET.get("reserva") or request.POST.get("reserva_id")
    reservas = Reserva.objects.select_related("cliente", "unidade").order_by("-id")
    if query:
        reservas = reservas.filter(
            Q(id__icontains=query)
            | Q(cliente__nome__icontains=query)
            | Q(cliente__telefone__icontains=query)
            | Q(cliente__email__icontains=query)
            | Q(unidade__codigo__icontains=query)
        )
    reservas = reservas[:30]

    reserva = None
    resumo = None
    if reserva_id:
        reserva = Reserva.objects.select_related("cliente", "unidade").filter(pk=reserva_id).first()
        if reserva:
            resumo = _resumo_reserva_faturacao(reserva)

    if request.method == "POST" and reserva:
        acao = request.POST.get("acao")
        if acao == "gerar_reserva":
            metodo = request.POST.get("metodo_pagamento") or ""
            fatura = gerar_fatura_automatica_reserva(
                reserva,
                emitido_por=request.user,
                tipo="integral" if metodo else "reserva",
                metodo_pagamento=metodo or None,
            )
            messages.success(request, f"Fatura da reserva gerada: {fatura.numero_fatura}")
            return redirect("faturacao:detalhe", fatura_id=fatura.id)
        if acao == "gerar_servicos":
            fatura = gerar_fatura_servicos_reserva(reserva, emitido_por=request.user, tipo="servicos")
            if not fatura:
                messages.info(request, "Não existem serviços pendentes de faturação para esta reserva.")
                return redirect(f"{request.path}?reserva={reserva.id}")
            messages.success(request, f"Fatura de serviços gerada: {fatura.numero_fatura}")
            return redirect("faturacao:detalhe", fatura_id=fatura.id)
        if acao == "gerar_final":
            fatura = gerar_fatura_servicos_reserva(reserva, emitido_por=request.user, tipo="final")
            if not fatura:
                fatura = gerar_fatura_automatica_reserva(reserva, emitido_por=request.user, tipo="final")
            messages.success(request, f"Fatura final gerada: {fatura.numero_fatura}")
            return redirect("faturacao:detalhe", fatura_id=fatura.id)

        if acao == "emitir_manual":
            item_forms = [ItemManualForm(request.POST, prefix=f"item{i}") for i in range(1, 4)]
            if all(i.is_valid() for i in item_forms):
                fatura = Fatura.objects.create(
                    cliente=reserva.cliente.user,
                    reserva=reserva,
                    tipo=request.POST.get("tipo_fatura") or "complementar",
                    status="emitida",
                    emitido_por=request.user,
                    observacoes="Pagamento prévio confirmado conforme política de reserva e serviços.",
                )
                for item in item_forms:
                    cd = item.cleaned_data
                    if (cd.get("descricao") or "").strip():
                        add_item_fatura(
                            fatura,
                            cd["descricao"],
                            cd["quantidade"],
                            cd["preco_unitario"],
                            origem_tipo="manual",
                            criado_por=request.user,
                            motivo_ajuste=request.POST.get("motivo_manual", "").strip(),
                        )
                recalcular_total_fatura(fatura)
                messages.success(request, f"Fatura manual complementar gerada: {fatura.numero_fatura}")
                return redirect("faturacao:detalhe", fatura_id=fatura.id)

    return render(
        request,
        "faturacao/emitir.html",
        {
            "form": form,
            "item_forms": item_forms,
            "reservas": reservas,
            "query": query,
            "reserva_selecionada": reserva,
            "resumo": resumo,
        },
    )


@interno_required
def detalhe(request, fatura_id: int):
    fatura = get_object_or_404(Fatura.objects.select_related("cliente", "reserva", "reserva__cliente"), pk=fatura_id)
    if request.method == "POST":
        acao = request.POST.get("acao")
        if acao == "registar_pagamento":
            metodo = request.POST.get("metodo_pagamento") or "presencial_recepcao"
            fatura.status = "paga"
            fatura.metodo_pagamento = metodo
            fatura.estado_pagamento = "validado"
            fatura.valor_pago = fatura.total
            fatura.pago_em = timezone.now()
            fatura.save(update_fields=["status", "metodo_pagamento", "estado_pagamento", "valor_pago", "pago_em", "valor_pendente"])
            messages.success(request, "Pagamento pré-pago registado com sucesso.")
        elif acao == "cancelar":
            if get_user_profile(request.user) != PERFIL_ADMINISTRADOR and not request.user.is_superuser:
                messages.error(request, "Apenas administradores podem cancelar faturas.")
                return redirect("faturacao:detalhe", fatura_id=fatura.id)
            fatura.status = "cancelada"
            fatura.save(update_fields=["status"])
            messages.warning(request, "Fatura cancelada.")
        elif acao == "enviar_email":
            ok = enviar_fatura_por_email_apos_pagamento(fatura)
            if ok:
                messages.success(request, "Fatura enviada por email.")
            else:
                messages.error(request, "Não foi possível enviar por email. Verifique o endereço do cliente.")
        elif acao == "enviar_whatsapp":
            fatura.enviado_whatsapp = True
            fatura.save(update_fields=["enviado_whatsapp"])
            messages.success(request, "Link de WhatsApp preparado para envio.")
            return redirect("faturacao:whatsapp", fatura_id=fatura.id)
        return redirect("faturacao:detalhe", fatura_id=fatura.id)
    return render(request, "faturacao/detalhe.html", {"fatura": fatura})


@interno_required
def imprimir(request, fatura_id: int):
    fatura = get_object_or_404(Fatura.objects.select_related("cliente", "reserva", "reserva__cliente"), pk=fatura_id)
    return render(request, "faturacao/imprimir.html", {"fatura": fatura})


@interno_required
def whatsapp(request, fatura_id: int):
    fatura = get_object_or_404(Fatura.objects.select_related("cliente", "reserva", "reserva__cliente"), pk=fatura_id)
    wa = getattr(settings, "RECECAO_WHATSAPP_MSISDN", "").replace(" ", "").replace("+", "")
    nome = fatura.reserva.cliente.nome if fatura.reserva_id else (fatura.cliente.get_full_name() or fatura.cliente.username)
    url_fatura = request.build_absolute_uri(f"/faturacao/{fatura.id}/imprimir/")
    texto = (
        f"Olá {nome}, segue a sua fatura {fatura.numero_fatura}. "
        f"Pode consultar/imprimir aqui: {url_fatura}"
    )
    link = f"https://wa.me/{wa}?text={quote(texto)}" if wa else ""
    return render(request, "faturacao/whatsapp.html", {"fatura": fatura, "whatsapp_link": link, "mensagem": texto})
