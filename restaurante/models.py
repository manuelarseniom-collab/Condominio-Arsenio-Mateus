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
    descricao = models.CharField(max_length=240, blank=True, default="")
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    imagem_url = models.URLField(blank=True, default="")
    tempo_preparo_min = models.PositiveSmallIntegerField(default=15)
    ativo = models.BooleanField(default=True)
    disponivel = models.BooleanField(default=True)
    controla_estoque = models.BooleanField(default=True)
    estoque_atual = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    estoque_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["categoria", "nome"]

    def __str__(self):
        return self.nome


class PedidoRestaurante(models.Model):
    ORIGEM = (
        ("quarto", "Pedido do quarto"),
        ("presencial", "Pedido presencial"),
        ("mesa_qr", "Pedido por QR Code"),
    )
    STATUS = (
        ("recebido", "Recebido"),
        ("aceite", "Aceite"),
        ("em_preparacao", "Em preparacao"),
        ("pronto", "Pronto"),
        ("entregue", "Entregue"),
        ("pago", "Pago"),
        ("cancelado", "Cancelado"),
    )

    reserva = models.ForeignKey(
        "reservas.Reserva",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_restaurante",
    )
    mesa = models.ForeignKey(
        "restaurante.MesaRestaurante",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos",
    )
    origem = models.CharField(max_length=20, choices=ORIGEM, default="quarto")
    cliente_nome = models.CharField(max_length=120, blank=True, default="")
    cliente_telefone = models.CharField(max_length=40, blank=True, default="")
    qr_code_usado = models.CharField(max_length=80, blank=True, default="")
    metodo_pagamento = models.CharField(max_length=40, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS, default="recebido")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    observacoes = models.CharField(max_length=240, blank=True, default="")
    tempo_estimado_min = models.PositiveSmallIntegerField(default=20)
    estoque_baixado = models.BooleanField(default=False)
    pago_em = models.DateTimeField(null=True, blank=True)
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


class MesaRestaurante(models.Model):
    ESTADO = (
        ("livre", "Livre"),
        ("ocupada", "Ocupada"),
        ("aguardando_atendimento", "Aguardando atendimento"),
    )

    numero = models.PositiveSmallIntegerField(unique=True)
    codigo_qr = models.CharField(max_length=30, unique=True)
    estado = models.CharField(max_length=30, choices=ESTADO, default="livre")

    class Meta:
        ordering = ["numero"]

    def __str__(self):
        return f"Mesa {self.numero}"

    @property
    def qr_image_url(self):
        # URL pública simples para renderizar QR sem dependências locais.
        return f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={self.codigo_qr}"


class MovimentoEstoqueRestaurante(models.Model):
    TIPO = (
        ("entrada", "Entrada"),
        ("saida", "Saída"),
        ("ajuste", "Ajuste"),
        ("reposicao", "Reposição"),
    )
    produto = models.ForeignKey(ProdutoRestaurante, on_delete=models.CASCADE, related_name="movimentos_estoque")
    pedido = models.ForeignKey(
        PedidoRestaurante,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentos_estoque",
    )
    tipo = models.CharField(max_length=20, choices=TIPO)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    observacao = models.CharField(max_length=255, blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.quantidade} - {self.produto.nome}"
