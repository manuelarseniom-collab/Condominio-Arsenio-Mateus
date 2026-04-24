from django.conf import settings
from django.db import models


class Servico(models.Model):
    codigo = models.SlugField(max_length=30, unique=True)
    nome = models.CharField(max_length=80)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class SolicitacaoServico(models.Model):
    class Status(models.TextChoices):
        SOLICITADO = "solicitado", "Solicitado"
        ATRIBUIDO = "atribuido", "Atribuido"
        EM_EXECUCAO = "em_execucao", "Em execucao"
        CONCLUIDO = "concluido", "Concluido"
        CANCELADO = "cancelado", "Cancelado"

    reserva = models.ForeignKey(
        "reservas.Reserva",
        on_delete=models.CASCADE,
        related_name="solicitacoes_servico",
    )
    servico = models.ForeignKey(
        Servico,
        on_delete=models.PROTECT,
        related_name="solicitacoes",
    )
    descricao = models.CharField(max_length=240, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SOLICITADO,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criado_em"]


class AtribuicaoStaff(models.Model):
    solicitacao = models.ForeignKey(
        SolicitacaoServico,
        on_delete=models.CASCADE,
        related_name="atribuicoes",
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tarefas_staff",
    )
    area = models.CharField(max_length=30)
    data_alvo = models.DateField(null=True, blank=True)
    concluida = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
