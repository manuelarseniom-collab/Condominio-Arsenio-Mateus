import logging
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def enviar_fatura_por_email_apos_pagamento(fatura) -> bool:
    """
    Envia resumo da fatura por email ao cliente após pagamento validado.
    WhatsApp: enviar link na mensagem para contacto da receção (envio manual ou integração futura).
    """
    reserva = fatura.reserva
    cliente = reserva.cliente
    email = (cliente.email or "").strip() or (cliente.user.email if cliente.user_id else "")
    if not email:
        logger.warning("Fatura %s: sem email de cliente para envio.", fatura.pk)
        return False

    wa = getattr(settings, "RECECAO_WHATSAPP_MSISDN", "").replace(" ", "").replace("+", "")
    wa_link = f"https://wa.me/{wa}" if wa else ""

    subject = f"Fatura #{fatura.pk} — Reserva #{reserva.pk} — Arsénio Mateus"
    body_lines = [
        f"Olá {cliente.nome},",
        "",
        f"A sua reserva #{reserva.pk} ({reserva.unidade.codigo}) foi confirmada após validação do pagamento.",
        f"Total da fatura: {Decimal(str(fatura.total)).quantize(Decimal('0.01'))} Kz.",
        "",
        "Pode consultar os detalhes na área reservada do portal.",
    ]
    if wa_link:
        body_lines.extend(
            [
                "",
                "Também pode solicitar o envio da fatura por WhatsApp à receção:",
                wa_link,
            ]
        )
    body = "\n".join(body_lines)

    try:
        send_mail(
            subject,
            body,
            getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
            [email],
            fail_silently=False,
        )
        return True
    except Exception as exc:  # pragma: no cover - SMTP variável
        logger.exception("Falha ao enviar email de fatura: %s", exc)
        return False
