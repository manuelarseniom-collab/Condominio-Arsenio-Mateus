from decimal import Decimal

from django.db import models


class PedidoLavandaria(models.Model):
    TIPO = (
        ("por_peca", "Por peca"),
        ("por_cesto", "Por cesto"),
    )
    STATUS = (
        ("pendente", "Pendente"),
        ("em_curso", "Em curso"),
        ("concluido", "Concluido"),
        ("cancelado", "Cancelado"),
    )

    PRECO_PECA = {
        "camisa": Decimal("2500"),
        "blusa": Decimal("2500"),
        "t-shirt": Decimal("2000"),
        "calcao": Decimal("2000"),
        "calcas": Decimal("3000"),
        "saia": Decimal("2500"),
        "vestido": Decimal("4000"),
        "casaco": Decimal("4500"),
        "fato": Decimal("7500"),
        "lencois": Decimal("4000"),
        "toalha": Decimal("2000"),
        "edredao": Decimal("8000"),
    }
    PRECO_CESTO = {
        "3": Decimal("2500"),
        "6": Decimal("4500"),
    }

    reserva = models.ForeignKey(
        "reservas.Reserva",
        on_delete=models.CASCADE,
        related_name="pedidos_lavandaria",
    )
    tipo = models.CharField(max_length=20, choices=TIPO, default="por_cesto")
    descricao = models.CharField(max_length=240)
    preco_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=STATUS, default="pendente")

    class Meta:
        ordering = ["-id"]

    def _calcular_preco(self) -> Decimal:
        from faturacao.services import preco_com_epoca

        mult = self.reserva.epoca.multiplicador if self.reserva.epoca_id else Decimal("1.00")
        d = self.descricao.lower()
        if self.tipo == "por_cesto":
            if "6" in d:
                base = self.PRECO_CESTO["6"]
            else:
                base = self.PRECO_CESTO["3"]
            return preco_com_epoca(base, mult)
        total = Decimal("0.00")
        for chave, preco in self.PRECO_PECA.items():
            if chave in d:
                total += preco
        if total == 0:
            total = self.PRECO_PECA["camisa"]
        return preco_com_epoca(total, mult)

    def save(self, *args, **kwargs):
        if self.preco_total == 0:
            self.preco_total = self._calcular_preco()
        super().save(*args, **kwargs)
