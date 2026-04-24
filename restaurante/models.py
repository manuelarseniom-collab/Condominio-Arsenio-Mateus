from decimal import Decimal

from django.db import models


class CategoriaProduto(models.Model):
    nome = models.CharField(max_length=80)
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["ordem", "nome"]

    def __str__(self):
        return self.nome


class ProdutoRestaurante(models.Model):
    categoria = models.ForeignKey(
        CategoriaProduto,
        on_delete=models.CASCADE,
        related_name="produtos",
    )
    nome = models.CharField(max_length=120)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["categoria", "nome"]

    def __str__(self):
        return self.nome


class PedidoRestaurante(models.Model):
    STATUS = (
        ("pendente", "Pendente"),
        ("em_preparacao", "Em preparacao"),
        ("entregue", "Entregue"),
        ("cancelado", "Cancelado"),
    )

    reserva = models.ForeignKey(
        "reservas.Reserva",
        on_delete=models.CASCADE,
        related_name="pedidos_restaurante",
    )
    status = models.CharField(max_length=20, choices=STATUS, default="pendente")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def recalcular_total(self) -> None:
        total = Decimal("0.00")
        for item in self.itens.select_related("produto"):
            total += item.subtotal
        self.total = total
        self.save(update_fields=["total"])


class ItemPedidoRestaurante(models.Model):
    pedido = models.ForeignKey(
        PedidoRestaurante,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    produto = models.ForeignKey(ProdutoRestaurante, on_delete=models.PROTECT)
    quantidade = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["id"]

    @property
    def subtotal(self) -> Decimal:
        from faturacao.services import preco_com_epoca

        mult = self.pedido.reserva.epoca.multiplicador if self.pedido.reserva.epoca_id else Decimal("1.00")
        unit = preco_com_epoca(self.produto.preco, mult)
        return (unit * Decimal(self.quantidade)).quantize(Decimal("0.01"))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
