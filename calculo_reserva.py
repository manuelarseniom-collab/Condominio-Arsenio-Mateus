"""
Cálculo único do valor total de uma reserva (período × preço mensal base).
Regra de negócio: base 30 dias/mês; meses alinhados por dia do mês vs. proporcional por dias.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Union

# Preço mensal de referência (Kz) por tipo de unidade — fonte única quando BD não tem preco_mensal.
PRECO_MENSAL_POR_TIPO: dict[str, float] = {
    "T1": 500_000.0,
    "T2": 750_000.0,
    "MASTER": 1_500_000.0,
    "ESCRITORIO": 200_000.0,
}


def preco_mensal_para_tipo(tipo_unidade: str | None) -> float | None:
    if not tipo_unidade:
        return None
    return PRECO_MENSAL_POR_TIPO.get(str(tipo_unidade).strip().upper())


def parse_data_reserva(d: Union[date, datetime, str]) -> date:
    if isinstance(d, date) and not isinstance(d, datetime):
        return d
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, str):
        s = d.strip()
        if len(s) >= 10:
            s = s[:10]
        return datetime.strptime(s, "%Y-%m-%d").date()
    raise TypeError(f"Tipo de data não suportado: {type(d)!r}")


def calcular_valor_reserva(
    valor_mensal: float,
    data_inicio: Union[date, datetime, str],
    data_fim: Union[date, datetime, str],
) -> float:
    """
    Valor total do período ocupado.
    - Se dia(início) == dia(fim): cobrança por meses completos de calendário.
    - Caso contrário: proporcional por dias (valor_mensal / 30 * dias).
    """
    if valor_mensal is None or float(valor_mensal) <= 0:
        raise ValueError("Unidade sem preço mensal definido")

    di = parse_data_reserva(data_inicio)
    df = parse_data_reserva(data_fim)

    if df <= di:
        raise ValueError("Data fim deve ser maior que data início")

    if di.day == df.day:
        meses = (df.year - di.year) * 12 + (df.month - di.month)
        valor_total = meses * float(valor_mensal)
    else:
        dias = (df - di).days
        valor_diario = float(valor_mensal) / 30.0
        valor_total = dias * valor_diario

    return round(float(valor_total), 2)


def quantidade_periodos_reserva(
    data_inicio: Union[date, datetime, str],
    data_fim: Union[date, datetime, str],
) -> int:
    """Meses de calendário (ramo dia==dia) ou número de dias (ramo proporcional)."""
    di = parse_data_reserva(data_inicio)
    df = parse_data_reserva(data_fim)
    if df <= di:
        raise ValueError("Data fim deve ser maior que data início")
    if di.day == df.day:
        return (df.year - di.year) * 12 + (df.month - di.month)
    return (df - di).days


def valor_mensal_efetivo(preco_mensal_col, tipo_unidade: str | None) -> float:
    """Usa coluna preco_mensal da unidade se > 0; senão tabela por tipo."""
    if preco_mensal_col is not None and float(preco_mensal_col) > 0:
        return float(preco_mensal_col)
    pm = preco_mensal_para_tipo(tipo_unidade)
    if pm is None:
        raise ValueError(f"Sem preço mensal para o tipo: {tipo_unidade!r}")
    return float(pm)


def executar_testes_calcular_valor_reserva() -> None:
    vm = 500_000.0
    assert calcular_valor_reserva(vm, date(2025, 1, 15), date(2025, 2, 15)) == 500_000.0
    assert calcular_valor_reserva(vm, date(2025, 1, 1), date(2025, 3, 1)) == 1_000_000.0

    vm2 = 300_000.0
    assert calcular_valor_reserva(vm2, date(2025, 1, 1), date(2025, 1, 16)) == 150_000.0

    try:
        calcular_valor_reserva(0, date(2025, 1, 1), date(2025, 1, 16))
    except ValueError:
        pass
    else:
        raise AssertionError("esperado ValueError para valor_mensal 0")

    try:
        calcular_valor_reserva(vm, date(2025, 1, 10), date(2025, 1, 10))
    except ValueError:
        pass
    else:
        raise AssertionError("esperado ValueError para data fim == início")

    um_dia = round(500_000.0 / 30.0 * 1, 2)
    assert calcular_valor_reserva(500_000.0, date(2025, 1, 1), date(2025, 1, 2)) == um_dia


if __name__ == "__main__":
    executar_testes_calcular_valor_reserva()
    print("testes calculo_reserva: OK")
