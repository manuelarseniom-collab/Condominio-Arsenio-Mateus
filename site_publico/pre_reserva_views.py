"""
Fluxo antigo em vários passos — redirecionado para pesquisa de disponibilidade.
Mantém apenas a página de sucesso após pré-reserva (novo fluxo em reservas.public_views).
"""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.conf import settings as dj_settings

from reservas.models import Reserva
from reservas.referencia_pagamento import formatar_instrucoes_pagamento


def pre_reserva_escolher_unidade(request):
    return redirect("buscar_apartamentos")


def pre_reserva_dados(request):
    return redirect("buscar_apartamentos")


def pre_reserva_conta(request):
    return redirect("buscar_apartamentos")


def pre_reserva_sucesso(request):
    rid = request.session.get("pre_reserva_concluida_id")
    reserva = None
    if rid:
        reserva = Reserva.objects.filter(pk=rid).select_related("cliente", "unidade").first()
    if not reserva:
        messages.info(request, "Inicie uma nova pré-reserva para obter a referência de pagamento.")
        return redirect("buscar_apartamentos")

    request.session.pop("pre_reserva_concluida_id", None)
    instr = formatar_instrucoes_pagamento(reserva)

    return render(
        request,
        "site_publico/pre_reserva_sucesso.html",
        {
            "reserva": reserva,
            "instrucoes_pagamento": instr,
            "whatsapp_rececao": getattr(dj_settings, "RECECAO_WHATSAPP_MSISDN", ""),
        },
    )
