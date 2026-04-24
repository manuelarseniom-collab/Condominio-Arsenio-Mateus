from decimal import Decimal

from django.db import models

from calculo_reserva import calcular_valor_reserva, valor_mensal_efetivo


class Reserva(models.Model):
    STATUS = (
        ("rascunho", "Rascunho"),
        ("pendente", "Pendente"),
        ("pre_reserva", "Pre-reserva"),
        ("aguardando_pagamento", "Aguardando pagamento"),
        ("pagamento_em_validacao", "Pagamento em validacao"),
        ("aguardando_confirmacao", "Aguardando confirmacao"),
        ("confirmada", "Confirmada"),
        ("ativa", "Ativa"),
        ("concluida", "Concluida"),
        ("cancelada", "Cancelada"),
    )

    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        related_name="reservas",
    )
    unidade = models.ForeignKey(
        "unidades.Unidade",
        on_delete=models.PROTECT,
        related_name="reservas",
    )
    data_inicio = models.DateField()
    data_fim = models.DateField()
    nome_completo = models.CharField(max_length=120, blank=True, default="")
    telefone = models.CharField(max_length=40, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    nacionalidade = models.CharField(max_length=80, blank=True, default="")
    tipo_documento = models.CharField(max_length=40, blank=True, default="")
    numero_documento_identificacao = models.CharField(max_length=60, blank=True, default="")
    data_nascimento = models.DateField(null=True, blank=True)
    morada = models.CharField(max_length=180, blank=True, default="")
    cidade = models.CharField(max_length=80, blank=True, default="")
    pais_residencia = models.CharField(max_length=80, blank=True, default="")
    contacto_alternativo = models.CharField(max_length=40, blank=True, default="")
    preferencia_contacto = models.CharField(max_length=20, blank=True, default="")
    numero_hospedes = models.PositiveSmallIntegerField(default=1)
    finalidade_estadia = models.CharField(max_length=120, blank=True, default="")
    observacoes = models.TextField(blank=True, default="")
    pedido_especial = models.TextField(blank=True, default="")
    valor_base = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=30, choices=STATUS, default="rascunho")
    epoca = models.ForeignKey(
        "faturacao.TabelaPreco",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reservas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    pagamento_entidade = models.CharField(
        max_length=5,
        blank=True,
        default="",
        help_text="Entidade bancária de referência (referência multibanco / similar).",
    )
    pagamento_referencia = models.CharField(
        max_length=12,
        blank=True,
        default="",
        db_index=True,
        help_text="Referência numérica associada ao pagamento da pré-reserva.",
    )
    pagamento_confirmado_whatsapp = models.BooleanField(
        default=False,
        help_text="Pagamento confirmado por WhatsApp.",
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"Reserva {self.pk} — {self.unidade.codigo}"

    def save(self, *args, **kwargs):
        from faturacao.models import TabelaPreco

        if not self.epoca_id:
            self.epoca = TabelaPreco.objects.filter(codigo="media").first() or self.epoca
        if self.unidade_id and self.data_inicio and self.data_fim and self.epoca_id:
            try:
                vm = valor_mensal_efetivo(self.unidade.preco_mensal, self.unidade.tipo)
                self.valor_base = Decimal(
                    str(
                        calcular_valor_reserva(
                            float(vm),
                            self.data_inicio.isoformat(),
                            self.data_fim.isoformat(),
                        )
                    )
                )
            except (ValueError, TypeError):
                pass
        if self.pagamento_confirmado_whatsapp:
            self.status = "confirmada"
        super().save(*args, **kwargs)
        if self.pagamento_confirmado_whatsapp:
            cliente = self.cliente
            changed = []
            if cliente.situacao_financeira != "paga":
                cliente.situacao_financeira = "paga"
                changed.append("situacao_financeira")
            if cliente.estado != "ativo":
                cliente.estado = "ativo"
                changed.append("estado")
            if changed:
                cliente.save(update_fields=changed)

    @property
    def habilita_area_cliente(self) -> bool:
        return self.status in ("confirmada", "ativa")
