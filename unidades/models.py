from django.db import models


class Unidade(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    nome = models.CharField(max_length=120)
    andar = models.PositiveSmallIntegerField(default=1)
    tipo = models.CharField(max_length=30)
    area_m2 = models.DecimalField(max_digits=10, decimal_places=2)
    preco_mensal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    disponivel = models.BooleanField(default=True)
    descricao = models.TextField(blank=True, default="")
    capacidade = models.PositiveSmallIntegerField(default=2)
    possui_sofa_cama = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True, default="")
    numero_quartos = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Número de quartos; se vazio, infere-se pela tipologia (T0..T3, penthouse).",
    )

    class Meta:
        ordering = ["andar", "codigo"]

    def __str__(self):
        return f"{self.codigo} — {self.nome}"

    @property
    def numero(self) -> str:
        return self.codigo

    @property
    def tipologia(self) -> str:
        return self.tipo

    @property
    def preco(self):
        return self.preco_mensal

    @property
    def ativo(self) -> bool:
        return self.disponivel

    @property
    def numero_quartos_efetivo(self) -> int:
        if self.numero_quartos is not None:
            return int(self.numero_quartos)
        t = (self.tipo or "").strip().upper()
        if t == "T0":
            return 0
        if t == "T1":
            return 1
        if t == "T2":
            return 2
        if t == "T3":
            return 3
        if "PENT" in t or "MASTER" in t:
            return 4
        return 0
