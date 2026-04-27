from decimal import Decimal

from django.db import models, transaction


def preco_com_epoca(preco_base: Decimal, multiplicador: Decimal) -> Decimal:
    return (Decimal(str(preco_base)) * Decimal(str(multiplicador))).quantize(Decimal("0.01"))


def recalcular_total_fatura(fatura) -> None:
    from faturacao.models import ItemFatura

    agg = ItemFatura.objects.filter(fatura=fatura).aggregate(s=models.Sum("total"))
    subtotal = agg["s"] or Decimal("0.00")
    desconto = Decimal(str(fatura.desconto or 0))
    total = max(Decimal("0.00"), Decimal(str(subtotal)) - desconto)
    fatura.subtotal = subtotal
    fatura.total = total
    fatura.valor_pendente = max(Decimal("0.00"), total - Decimal(str(fatura.valor_pago or 0)))
    fatura.save(update_fields=["subtotal", "total", "valor_pendente"])


def add_item_fatura(
    fatura,
    descricao: str,
    quantidade,
    preco_unitario: Decimal,
    origem_tipo: str = "manual",
    origem_id: int | None = None,
    criado_por=None,
    motivo_ajuste: str = "",
) -> None:
    from faturacao.models import ItemFatura

    q = Decimal(str(quantidade))
    pu = Decimal(str(preco_unitario))
    ItemFatura.objects.create(
        fatura=fatura,
        descricao=descricao,
        quantidade=int(q),
        preco_unitario=pu,
        origem_tipo=origem_tipo,
        origem_id=origem_id,
        criado_por=criado_por,
        motivo_ajuste=motivo_ajuste,
    )


@transaction.atomic
def criar_fatura_base_para_reserva(reserva) -> None:
    """Garante fatura e linha de estadia (valor_base) para uma reserva nova."""
    from faturacao.models import Fatura, ItemFatura

    fatura = obter_fatura_principal_reserva(reserva)
    if not fatura:
        fatura = Fatura.objects.create(
            reserva=reserva,
            cliente=reserva.cliente.user,
            total=Decimal("0.00"),
            status="emitida",
        )
    if not ItemFatura.objects.filter(fatura=fatura, descricao="Estadia").exists():
        add_item_fatura(
            fatura,
            "Estadia",
            1,
            Decimal(str(reserva.valor_base)),
            origem_tipo="reserva",
            origem_id=reserva.id,
        )


def obter_fatura_principal_reserva(reserva):
    from faturacao.models import Fatura

    return (
        Fatura.objects.filter(reserva=reserva)
        .order_by("id")
        .first()
    )


def _servicos_pendentes_reserva(reserva):
    from faturacao.models import ItemFatura

    itens = []
    limpeza_ids = set(
        ItemFatura.objects.filter(fatura__reserva=reserva, origem_tipo="limpeza").values_list("origem_id", flat=True)
    )
    for p in reserva.pedidos_limpeza.exclude(status="cancelado"):
        if p.id not in limpeza_ids:
            itens.append(("limpeza", p.id, f"Serviço de limpeza #{p.id}", 1, p.preco))

    lav_ids = set(
        ItemFatura.objects.filter(fatura__reserva=reserva, origem_tipo="lavandaria").values_list("origem_id", flat=True)
    )
    for p in reserva.pedidos_lavandaria.exclude(status="cancelado"):
        if p.id not in lav_ids:
            itens.append(("lavandaria", p.id, f"Serviço de lavandaria #{p.id}", 1, p.preco_total))

    rest_ids = set(
        ItemFatura.objects.filter(fatura__reserva=reserva, origem_tipo="restaurante").values_list("origem_id", flat=True)
    )
    for p in reserva.pedidos_restaurante.exclude(status="cancelado"):
        if p.id not in rest_ids:
            itens.append(("restaurante", p.id, f"Consumo restaurante #{p.id}", 1, p.total))
    return itens


@transaction.atomic
def gerar_fatura_automatica_reserva(reserva, emitido_por=None, tipo="reserva", metodo_pagamento=None):
    from faturacao.models import Fatura, ItemFatura

    fatura = Fatura.objects.create(
        reserva=reserva,
        cliente=reserva.cliente.user,
        tipo=tipo,
        metodo_pagamento=metodo_pagamento or "",
        emitido_por=emitido_por,
        estado_pagamento="validado" if metodo_pagamento else "pendente",
        observacoes="Pagamento prévio confirmado conforme política de reserva e serviços.",
    )
    add_item_fatura(
        fatura,
        f"Alojamento {reserva.unidade.tipo} ({reserva.data_inicio} a {reserva.data_fim})",
        1,
        Decimal(str(reserva.valor_base)),
        origem_tipo="reserva",
        origem_id=reserva.id,
        criado_por=emitido_por,
    )
    recalcular_total_fatura(fatura)
    if metodo_pagamento:
        fatura.status = "paga"
        fatura.valor_pago = fatura.total
        fatura.estado_pagamento = "validado"
        fatura.save(update_fields=["status", "valor_pago", "estado_pagamento", "valor_pendente", "pago_em"])
    return fatura


@transaction.atomic
def gerar_fatura_servicos_reserva(reserva, emitido_por=None, tipo="servicos"):
    from faturacao.models import Fatura

    pendentes = _servicos_pendentes_reserva(reserva)
    if not pendentes:
        return None
    fatura = Fatura.objects.create(
        reserva=reserva,
        cliente=reserva.cliente.user,
        tipo=tipo,
        emitido_por=emitido_por,
        observacoes="Pagamento prévio confirmado conforme política de reserva e serviços.",
    )
    for origem_tipo, origem_id, descricao, qtd, pu in pendentes:
        add_item_fatura(
            fatura,
            descricao,
            qtd,
            pu,
            origem_tipo=origem_tipo,
            origem_id=origem_id,
            criado_por=emitido_por,
        )
    recalcular_total_fatura(fatura)
    return fatura
