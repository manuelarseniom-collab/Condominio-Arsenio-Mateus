from decimal import Decimal

from django.db import models


class PedidoLimpeza(models.Model):
    TIPO = (
        ("normal", "Normal"),
        ("profunda", "Profunda"),
        ("checkout", "Checkout"),
    )
    STATUS = (
        ("pendente", "Pendente"),
        ("em_curso", "Em curso"),
        ("concluido", "Concluido"),
        ("cancelado", "Cancelado"),
    )

    PRECO_BASE = {
        "normal": Decimal("10000"),
        "profunda": Decimal("18000"),
        "checkout": Decimal("25000"),
    }

    reserva = models.ForeignKey(
        "reservas.Reserva",
        on_delete=models.CASCADE,
        related_name="pedidos_limpeza",
    )
    data = models.DateField()
    tipo = models.CharField(max_length=20, choices=TIPO, default="normal")
    preco = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=STATUS, default="pendente")

    class Meta:
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        from faturacao.services import preco_com_epoca

        base = self.PRECO_BASE.get(self.tipo, Decimal("10000"))
        mult = self.reserva.epoca.multiplicador if self.reserva.epoca_id else Decimal("1.00")
        self.preco = preco_com_epoca(base, mult)
        super().save(*args, **kwargs)
