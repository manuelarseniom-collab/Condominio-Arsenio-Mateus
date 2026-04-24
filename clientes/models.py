from django.conf import settings
from django.db import models


class Cliente(models.Model):
    ESTADO_CHOICES = (
        ("interessado", "Interessado"),
        ("ativo", "Ativo"),
        ("inativo", "Inativo"),
    )
    SITUACAO_FINANCEIRA_CHOICES = (
        ("por_pagar", "Por pagar"),
        ("em_validacao", "Em validacao"),
        ("paga", "Paga"),
    )

    """Hospede / cliente do condominio (ligacao opcional a utilizador do portal)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="perfil_cliente",
    )
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    nacionalidade = models.CharField(max_length=80, blank=True, default="")
    tipo_documento = models.CharField(max_length=40, blank=True, default="")
    numero_documento_identificacao = models.CharField(max_length=60, blank=True, default="")
    data_nascimento = models.DateField(null=True, blank=True)
    morada = models.CharField(max_length=180, blank=True, default="")
    cidade = models.CharField(max_length=80, blank=True, default="")
    pais_residencia = models.CharField(max_length=80, blank=True, default="")
    empresa_instituicao = models.CharField(max_length=120, blank=True, default="")
    contacto_alternativo = models.CharField(max_length=40, blank=True, default="")
    preferencia_contacto = models.CharField(max_length=20, blank=True, default="")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="interessado")
    situacao_financeira = models.CharField(
        max_length=20,
        choices=SITUACAO_FINANCEIRA_CHOICES,
        default="por_pagar",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.nome
