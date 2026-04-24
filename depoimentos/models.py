from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Depoimento(models.Model):
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("aprovado", "Aprovado"),
        ("rejeitado", "Rejeitado"),
        ("oculto", "Oculto"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="depoimentos",
    )
    reserva = models.ForeignKey(
        "reservas.Reserva",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="depoimentos",
    )
    titulo = models.CharField(max_length=120)
    comentario = models.TextField()
    avaliacao = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendente")
    publicado = models.BooleanField(default=False)
    abusivo = models.BooleanField(default=False)
    motivo_moderacao = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "reserva"],
                name="uniq_depoimento_por_user_reserva",
            )
        ]

    def __str__(self):
        return f"{self.titulo} - {self.user}"
