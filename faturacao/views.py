from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from faturacao.models import Fatura
from faturacao.notificacoes import enviar_fatura_por_email_apos_pagamento
from faturacao.services import add_item_fatura, recalcular_total_fatura
from usuarios.authz import interno_required
from usuarios.roles import PERFIL_ADMINISTRADOR, get_user_profile

from .forms import FaturaForm, ItemManualForm

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
    if request.method == "POST":
        form = FaturaForm(request.POST)
        item_forms = [ItemManualForm(request.POST, prefix=f"item{i}") for i in range(1, 4)]
        if form.is_valid() and all(i.is_valid() for i in item_forms):
            cliente = form.cleaned_data["cliente"]
            reserva = form.cleaned_data.get("reserva")
            incluir_reserva = form.cleaned_data["incluir_reserva"]
            fatura = Fatura.objects.create(
                cliente=cliente.user,
                reserva=reserva,
                status="emitida",
                emitido_por=request.user,
            )
            if incluir_reserva and reserva:
                add_item_fatura(fatura, f"Alojamento ({reserva.unidade.tipo})", 1, reserva.valor_base)
            for item in item_forms:
                cd = item.cleaned_data
                if (cd.get("descricao") or "").strip():
                    add_item_fatura(fatura, cd["descricao"], cd["quantidade"], cd["preco_unitario"])
            recalcular_total_fatura(fatura)
            messages.success(request, f"Fatura {fatura.numero_fatura} emitida com sucesso.")
            return redirect("faturacao:detalhe", fatura_id=fatura.id)
    else:
        form = FaturaForm()
    return render(
        request,
        "faturacao/emitir.html",
        {"form": form, "item_forms": item_forms},
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
            fatura.pago_em = timezone.now()
            fatura.save(update_fields=["status", "metodo_pagamento", "pago_em"])
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
