"""
Regras de disponibilidade e anti-overbooking para unidades habitacionais.
"""

from django.db.models import Exists, OuterRef, Q

from reservas.models import Reserva


# Reservas nestes estados ocupam o apartamento no intervalo de datas (conflito).
ESTADOS_OCUPAM_AGENDA = frozenset(
    {
        "pre_reserva",
        "aguardando_pagamento",
        "pagamento_em_validacao",
        "confirmada",
        "ativa",
    }
)


def reservas_em_conflito_no_periodo(unidade_id: int, data_inicio, data_fim):
    """Queryset de reservas que se sobrepõem ao intervalo [data_inicio, data_fim] para a unidade."""
    if data_inicio >= data_fim:
        return Reserva.objects.none()
    return Reserva.objects.filter(
        unidade_id=unidade_id,
        status__in=ESTADOS_OCUPAM_AGENDA,
    ).filter(Q(data_inicio__lt=data_fim) & Q(data_fim__gt=data_inicio))


def unidade_disponivel_no_periodo(unidade_id: int, data_inicio, data_fim) -> bool:
    """True se não existir reserva bloqueante sobreposta ao período."""
    return not reservas_em_conflito_no_periodo(unidade_id, data_inicio, data_fim).exists()


def apartamentos_disponiveis(data_entrada, data_saida, tipologia=None, andar=None):
    """
    Unidades livres no período, com filtros opcionais.
    Ordenação: andar, código (identificador do apartamento).
    """
    from unidades.models import Unidade

    if data_entrada >= data_saida:
        return Unidade.objects.none()

    qs = Unidade.objects.filter(disponivel=True)

    if tipologia:
        t = tipologia.strip().upper()
        if t in ("PENTHOUSE", "MASTER"):
            qs = qs.filter(Q(tipo__icontains="pent") | Q(tipo__icontains="master"))
        else:
            qs = qs.filter(tipo__iexact=t)

    if andar is not None and andar != "":
        qs = qs.filter(andar=int(andar))

    conflito = Reserva.objects.filter(
        unidade_id=OuterRef("pk"),
        status__in=ESTADOS_OCUPAM_AGENDA,
        data_inicio__lt=data_saida,
        data_fim__gt=data_entrada,
    )
    qs = qs.annotate(_tem_conflito=Exists(conflito)).filter(_tem_conflito=False)

    return qs.order_by("andar", "codigo")
