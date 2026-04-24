import secrets
from decimal import Decimal

from django.conf import settings


def gerar_referencia_pagamento(reserva) -> tuple[str, str]:
    """
    Gera entidade e referência para pagamento (formato simplificado para integração futura).
    Valor a liquidar = reserva.valor_base (também na fatura).
    """
    entidade = getattr(settings, "PAGAMENTO_ENTIDADE_REF", "12345")[:5].zfill(5)
    modelo = reserva.__class__
    for _ in range(50):
        ref = "".join(str(secrets.randbelow(10)) for _ in range(9))
        if not modelo.objects.filter(pagamento_referencia=ref).exists():
            return entidade, ref
    ref = f"{reserva.pk:09d}"[-9:]
    return entidade, ref


def formatar_instrucoes_pagamento(reserva) -> str:
    valor = Decimal(str(reserva.valor_base)).quantize(Decimal("0.01"))
    return (
        f"Entidade: {reserva.pagamento_entidade} | "
        f"Referência: {reserva.pagamento_referencia} | "
        f"Valor: {valor} Kz. "
        "Após o pagamento ser validado, a reserva passa a confirmada e receberá a fatura por email ou WhatsApp."
    )
