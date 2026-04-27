from django.contrib import admin

from .models import Fatura, ItemFatura, Pagamento, TabelaPreco


@admin.register(TabelaPreco)
class TabelaPrecoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "multiplicador")


class ItemFaturaInline(admin.TabularInline):
    model = ItemFatura
    extra = 0


@admin.register(Fatura)
class FaturaAdmin(admin.ModelAdmin):
    list_display = (
        "numero_fatura",
        "tipo",
        "cliente",
        "reserva",
        "data_emissao",
        "total",
        "valor_pago",
        "valor_pendente",
        "status",
        "estado_pagamento",
    )
    list_filter = ("tipo", "status", "estado_pagamento", "metodo_pagamento", "enviado_email", "enviado_whatsapp", "data_emissao")
    search_fields = ("numero_fatura", "reserva__id", "cliente__username", "cliente__email")
    inlines = [ItemFaturaInline]


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ("id", "fatura", "valor", "data", "metodo")
