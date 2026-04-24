from django.conf import settings
from django.db import models


class PerfilAcesso(models.TextChoices):
    VISITANTE = "visitante", "Visitante"
    CLIENTE_PENDENTE = "cliente_pendente", "Cliente pendente"
    CLIENTE_CONFIRMADO = "cliente_confirmado", "Cliente confirmado"
    STAFF_LIMPEZA = "staff_limpeza", "Staff limpeza"
    STAFF_LAVANDARIA = "staff_lavandaria", "Staff lavandaria"
    STAFF_RESTAURANTE = "staff_restaurante", "Staff restaurante"
    STAFF_MANUTENCAO = "staff_manutencao", "Staff manutencao"
    RECEPCAO = "recepcao", "Recepcao"
    ADMIN = "admin", "Admin"
    ADMIN_CONDOMINIO = "admin_condominio", "Admin condominio"
    ADMIN_SISTEMA = "admin_sistema", "Admin sistema"


class PerfilUsuario(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_acesso",
    )
    role = models.CharField(
        max_length=40,
        choices=PerfilAcesso.choices,
        default=PerfilAcesso.VISITANTE,
    )
    telefone = models.CharField(max_length=40, blank=True)
    departamento = models.CharField(max_length=60, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Notificacao(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificacoes",
    )
    titulo = models.CharField(max_length=120)
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.user.username}: {self.titulo}"
