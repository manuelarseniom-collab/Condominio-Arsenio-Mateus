from django.contrib import admin

from .models import PedidoLimpeza


@admin.register(PedidoLimpeza)
class PedidoLimpezaAdmin(admin.ModelAdmin):
    list_display = ("id", "reserva", "data", "tipo", "preco", "status")
