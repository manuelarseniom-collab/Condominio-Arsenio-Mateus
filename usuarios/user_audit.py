"""
Utilitários para auditoria de utilizadores sem expor segredos (passwords ou hashes).
"""

from __future__ import annotations

import csv
import secrets
import string
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Iterator, TextIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone


User = get_user_model()


@dataclass(frozen=True)
class LinhaAuditoriaUtilizador:
    username: str
    email: str
    is_staff: bool
    is_superuser: bool
    is_active: bool
    last_login: datetime | None
    date_joined: datetime | None
    password_definida: bool

    @classmethod
    def a_partir_de_user(cls, user: AbstractBaseUser) -> LinhaAuditoriaUtilizador:
        return cls(
            username=user.get_username(),
            email=(user.email or "").strip(),
            is_staff=bool(user.is_staff),
            is_superuser=bool(user.is_superuser),
            is_active=bool(user.is_active),
            last_login=user.last_login,
            date_joined=getattr(user, "date_joined", None),
            password_definida=user.has_usable_password(),
        )


def iter_linhas_auditoria() -> Iterator[LinhaAuditoriaUtilizador]:
    qs = User._default_manager.all().order_by("username")
    for u in qs.iterator():
        yield LinhaAuditoriaUtilizador.a_partir_de_user(u)


def _fmt_sim_nao(val: bool) -> str:
    return "SIM" if val else "NAO"


def _fmt_data(dt: datetime | None) -> str:
    if dt is None:
        return "-"
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return dt.strftime("%Y-%m-%d %H:%M")


def formatar_linha_texto(linha: LinhaAuditoriaUtilizador, separador: str = " | ") -> str:
    return separador.join(
        [
            linha.username,
            linha.email or "-",
            _fmt_sim_nao(linha.is_staff),
            _fmt_sim_nao(linha.is_superuser),
            _fmt_sim_nao(linha.is_active),
            _fmt_sim_nao(linha.password_definida),
            _fmt_data(linha.last_login),
            _fmt_data(linha.date_joined),
        ]
    )


CABECALHO_TXT = (
    "USERNAME | EMAIL | STAFF | SUPERUSER | ATIVO | PASSWORD_DEFINIDA | ULTIMO_LOGIN | DATA_REGISTO"
)


def resumo_utilizadores(linhas: Iterable[LinhaAuditoriaUtilizador]) -> tuple[int, int, int, int]:
    total = 0
    superusers = 0
    staff = 0
    ativos = 0
    for l in linhas:
        total += 1
        if l.is_superuser:
            superusers += 1
        if l.is_staff:
            staff += 1
        if l.is_active:
            ativos += 1
    return total, superusers, staff, ativos


def escrever_csv(caminho: str, linhas: Iterable[LinhaAuditoriaUtilizador]) -> None:
    fieldnames = [
        "username",
        "email",
        "is_staff",
        "is_superuser",
        "is_active",
        "password_definida",
        "last_login",
        "date_joined",
    ]
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for l in linhas:
            w.writerow(
                {
                    "username": l.username,
                    "email": l.email,
                    "is_staff": l.is_staff,
                    "is_superuser": l.is_superuser,
                    "is_active": l.is_active,
                    "password_definida": l.password_definida,
                    "last_login": l.last_login.isoformat() if l.last_login else "",
                    "date_joined": l.date_joined.isoformat() if l.date_joined else "",
                }
            )


def escrever_txt(caminho: str, linhas: Iterable[LinhaAuditoriaUtilizador], stream: TextIO | None = None) -> None:
    if stream is not None:
        out = stream
        close = False
    else:
        out = open(caminho, "w", encoding="utf-8")
        close = True
    try:
        out.write(CABECALHO_TXT + "\n")
        out.write("-" * len(CABECALHO_TXT) + "\n")
        for linha in linhas:
            out.write(formatar_linha_texto(linha=linha) + "\n")
    finally:
        if close:
            out.close()


def gerar_password_aleatoria(tamanho: int = 16) -> str:
    """Gera password forte sem caracteres ambíguos para cópia manual."""
    alfabeto = string.ascii_letters + string.digits
    return "".join(secrets.choice(alfabeteto) for _ in range(tamanho))
