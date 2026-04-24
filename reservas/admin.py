from django.contrib import admin

from .models import Reserva


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cliente",
        "unidade",
        "data_inicio",
        "data_fim",
        "valor_base",
        "status",
        "pagamento_confirmado_whatsapp",
        "epoca",
    )
