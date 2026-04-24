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
    list_display = ("id", "reserva", "data_emissao", "total", "status")
    inlines = [ItemFaturaInline]


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ("id", "fatura", "valor", "data", "metodo")
