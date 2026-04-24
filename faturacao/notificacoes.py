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
    cliente = reserva.cliente if reserva else None
    email = ""
    if cliente:
        email = (cliente.email or "").strip() or (cliente.user.email if cliente.user_id else "")
    elif fatura.cliente_id:
        email = (fatura.cliente.email or "").strip()
    if not email:
        logger.warning("Fatura %s: sem email de cliente para envio.", fatura.pk)
        return False

    wa = getattr(settings, "RECECAO_WHATSAPP_MSISDN", "").replace(" ", "").replace("+", "")
    wa_link = f"https://wa.me/{wa}" if wa else ""

    ref_reserva = f"Reserva #{reserva.pk}" if reserva else "Sem reserva associada"
    subject = f"Fatura {fatura.numero_fatura or f'#{fatura.pk}'} — {ref_reserva} — Arsénio Mateus"
    nome_cliente = cliente.nome if cliente else (fatura.cliente.get_full_name() or fatura.cliente.username)
    body_lines = [
        f"Olá {nome_cliente},",
        "",
        f"{ref_reserva} foi confirmada após validação do pagamento." if reserva else "A sua fatura foi emitida.",
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
        fatura.enviado_email = True
        fatura.save(update_fields=["enviado_email"])
        return True
    except Exception as exc:  # pragma: no cover - SMTP variável
        logger.exception("Falha ao enviar email de fatura: %s", exc)
        return False
