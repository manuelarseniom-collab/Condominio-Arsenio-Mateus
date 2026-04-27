from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone

from usuarios.models import PerfilAcesso, PerfilUsuario


class TabelaPreco(models.Model):
    """Epoca / tabela de multiplicador aplicada a precos de servicos."""

    codigo = models.SlugField(max_length=20, unique=True)
    nome = models.CharField(max_length=60)
    multiplicador = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("1.00"))

    class Meta:
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.nome} (x{self.multiplicador})"


class Fatura(models.Model):
    TIPO = (
        ("reserva", "Fatura de reserva"),
        ("sinal", "Fatura de sinal"),
        ("integral", "Fatura de pagamento integral"),
        ("servicos", "Fatura de serviços"),
        ("complementar", "Fatura complementar"),
        ("final", "Fatura final"),
    )
    STATUS = (
        ("emitida", "Emitida"),
        ("paga", "Paga"),
        ("cancelada", "Cancelada"),
    )
    ESTADO_PAGAMENTO = (
        ("pendente", "Pendente"),
        ("pago", "Pago"),
        ("validado", "Validado"),
    )

    cliente = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="faturas_emitidas",
    )
    reserva = models.ForeignKey(
        "reservas.Reserva",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faturas",
    )
    numero_fatura = models.CharField(max_length=50, unique=True, blank=True, null=True)
    data_emissao = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=20, choices=TIPO, default="reserva")
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    desconto = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    valor_pago = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    valor_pendente = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=STATUS, default="emitida")
    estado_pagamento = models.CharField(max_length=20, choices=ESTADO_PAGAMENTO, default="pendente")
    metodo_pagamento = models.CharField(max_length=50, blank=True, null=True)
    referencia_pagamento = models.CharField(max_length=50, blank=True, null=True)
    pago_em = models.DateTimeField(blank=True, null=True)
    observacoes = models.TextField(blank=True, default="")
    enviado_email = models.BooleanField(default=False)
    enviado_whatsapp = models.BooleanField(default=False)
    emitido_por = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faturas_criadas",
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.numero_fatura or f"Fatura #{self.pk}"

    @classmethod
    def proximo_numero_fatura(cls):
        ano = timezone.now().year
        prefixo = f"FT-{ano}-"
        ultima = (
            cls.objects.filter(numero_fatura__startswith=prefixo)
            .order_by("-numero_fatura")
            .values_list("numero_fatura", flat=True)
            .first()
        )
        sequencia = 1
        if ultima:
            try:
                sequencia = int(ultima.split("-")[-1]) + 1
            except (ValueError, IndexError):
                sequencia = 1
        return f"{prefixo}{sequencia:04d}"

    def save(self, *args, **kwargs):
        if not self.numero_fatura:
            self.numero_fatura = self.proximo_numero_fatura()
        if not self.cliente_id and self.reserva_id and self.reserva.cliente.user_id:
            self.cliente = self.reserva.cliente.user
        if self.desconto < 0:
            self.desconto = Decimal("0.00")
        if self.valor_pago < 0:
            self.valor_pago = Decimal("0.00")
        self.valor_pendente = max(Decimal("0.00"), Decimal(str(self.total)) - Decimal(str(self.valor_pago)))
        if self.estado_pagamento in {"pago", "validado"} and self.valor_pago <= 0:
            self.valor_pago = self.total
            self.valor_pendente = Decimal("0.00")
        if self.status == "paga" and not self.pago_em:
            self.pago_em = timezone.now()
        super().save(*args, **kwargs)


class ItemFatura(models.Model):
    ORIGEM = (
        ("reserva", "Reserva"),
        ("limpeza", "Limpeza"),
        ("lavandaria", "Lavandaria"),
        ("restaurante", "Restaurante"),
        ("extensao", "Extensão"),
        ("manual", "Manual"),
    )
    fatura = models.ForeignKey(Fatura, on_delete=models.CASCADE, related_name="itens")
    descricao = models.CharField(max_length=200)
    quantidade = models.IntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    origem_tipo = models.CharField(max_length=20, choices=ORIGEM, default="manual")
    origem_id = models.PositiveIntegerField(null=True, blank=True)
    criado_por = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="itens_fatura_criados",
    )
    motivo_ajuste = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.descricao

    def subtotal(self):
        return (Decimal(str(self.quantidade)) * Decimal(str(self.preco_unitario))).quantize(Decimal("0.01"))

    def save(self, *args, **kwargs):
        self.total = self.subtotal()
        super().save(*args, **kwargs)


class Pagamento(models.Model):
    STATUS = (
        ("pendente", "Pendente"),
        ("aprovado", "Aprovado"),
        ("recusado", "Recusado"),
    )

    fatura = models.ForeignKey(Fatura, on_delete=models.CASCADE, related_name="pagamentos")
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    data = models.DateTimeField(auto_now_add=True)
    metodo = models.CharField(max_length=60)
    status = models.CharField(max_length=20, choices=STATUS, default="pendente")

    def __str__(self):
        return f"Pago {self.valor} em {self.data.date()}"

    @staticmethod
    def _garantir_acesso_cliente_confirmado(reserva):
        cliente = reserva.cliente
        email = (cliente.email or "").strip().lower()
        if not email:
            return

        with transaction.atomic():
            user = cliente.user
            User = get_user_model()
            if not user:
                user = User.objects.filter(username__iexact=email).first()
            if not user:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=None,
                    is_active=True,
                )
                user.set_unusable_password()
                user.save(update_fields=["password"])
            if cliente.user_id != user.id:
                cliente.user = user
                cliente.save(update_fields=["user"])

            perfil, _ = PerfilUsuario.objects.get_or_create(
                user=user,
                defaults={"role": PerfilAcesso.CLIENTE_CONFIRMADO},
            )
            if perfil.role != PerfilAcesso.CLIENTE_CONFIRMADO:
                perfil.role = PerfilAcesso.CLIENTE_CONFIRMADO
                perfil.save(update_fields=["role"])

    def save(self, *args, **kwargs):
        prev_status = None
        if self.pk:
            anterior = Pagamento.objects.filter(pk=self.pk).only("status").first()
            if anterior:
                prev_status = anterior.status
        super().save(*args, **kwargs)
        if self.status == "aprovado":
            reserva = self.fatura.reserva
            if reserva:
                if reserva.status in (
                    "pendente",
                    "pre_reserva",
                    "aguardando_pagamento",
                    "pagamento_em_validacao",
                    "aguardando_confirmacao",
                    "rascunho",
                ):
                    reserva.status = "confirmada"
                    reserva.save(update_fields=["status"])
                cliente = reserva.cliente
                cliente_updates = []
                if cliente.situacao_financeira != "paga":
                    cliente.situacao_financeira = "paga"
                    cliente_updates.append("situacao_financeira")
                if reserva.status == "confirmada" and cliente.estado != "ativo":
                    cliente.estado = "ativo"
                    cliente_updates.append("estado")
                if cliente_updates:
                    cliente.save(update_fields=cliente_updates)
                self._garantir_acesso_cliente_confirmado(reserva)
            self.fatura.status = "paga"
            self.fatura.metodo_pagamento = self.metodo
            self.fatura.estado_pagamento = "validado"
            self.fatura.valor_pago = self.valor
            self.fatura.pago_em = timezone.now()
            self.fatura.save(update_fields=["status", "metodo_pagamento", "estado_pagamento", "valor_pago", "pago_em", "valor_pendente"])
            if prev_status != "aprovado":
                from faturacao.notificacoes import enviar_fatura_por_email_apos_pagamento

                enviar_fatura_por_email_apos_pagamento(self.fatura)
