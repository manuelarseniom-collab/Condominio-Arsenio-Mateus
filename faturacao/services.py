from decimal import Decimal

from django.db import models, transaction


def preco_com_epoca(preco_base: Decimal, multiplicador: Decimal) -> Decimal:
    return (Decimal(str(preco_base)) * Decimal(str(multiplicador))).quantize(Decimal("0.01"))


def recalcular_total_fatura(fatura) -> None:
    from faturacao.models import ItemFatura

    agg = ItemFatura.objects.filter(fatura=fatura).aggregate(s=models.Sum("total"))
    total = agg["s"] or Decimal("0.00")
    fatura.total = total
    fatura.save(update_fields=["total"])


def add_item_fatura(fatura, descricao: str, quantidade, preco_unitario: Decimal) -> None:
    from faturacao.models import ItemFatura

    q = Decimal(str(quantidade))
    pu = Decimal(str(preco_unitario))
    ItemFatura.objects.create(
        fatura=fatura,
        descricao=descricao,
        quantidade=int(q),
        preco_unitario=pu,
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
        )


def obter_fatura_principal_reserva(reserva):
    from faturacao.models import Fatura

    return (
        Fatura.objects.filter(reserva=reserva)
        .order_by("id")
        .first()
    )
