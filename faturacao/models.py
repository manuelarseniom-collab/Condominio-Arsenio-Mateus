from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models, transaction

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
    STATUS = (
        ("rascunho", "Rascunho"),
        ("pendente", "Pendente"),
        ("paga", "Paga"),
        ("cancelada", "Cancelada"),
    )

    reserva = models.OneToOneField(
        "reservas.Reserva",
        on_delete=models.CASCADE,
        related_name="fatura",
    )
    data_emissao = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=STATUS, default="pendente")

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"Fatura #{self.pk} — {self.reserva_id}"


class ItemFatura(models.Model):
    fatura = models.ForeignKey(Fatura, on_delete=models.CASCADE, related_name="itens")
    descricao = models.CharField(max_length=200)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1"))
    preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.descricao


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
            if prev_status != "aprovado":
                from faturacao.notificacoes import enviar_fatura_por_email_apos_pagamento

                enviar_fatura_por_email_apos_pagamento(self.fatura)
