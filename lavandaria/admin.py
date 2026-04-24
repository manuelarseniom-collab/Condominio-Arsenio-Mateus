from django.contrib import admin

from .models import PedidoLavandaria


@admin.register(PedidoLavandaria)
class PedidoLavandariaAdmin(admin.ModelAdmin):
    list_display = ("id", "reserva", "tipo", "preco_total", "status")
