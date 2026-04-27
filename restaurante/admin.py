from django.contrib import admin

from .models import (
    CategoriaProduto,
    ItemPedidoRestaurante,
    MesaRestaurante,
    MovimentoEstoqueRestaurante,
    PedidoRestaurante,
    ProdutoRestaurante,
)


@admin.register(CategoriaProduto)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ordem")


@admin.register(ProdutoRestaurante)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "categoria",
        "preco",
        "estoque_atual",
        "estoque_minimo",
        "disponivel",
        "tempo_preparo_min",
        "ativo",
    )


class ItemInline(admin.TabularInline):
    model = ItemPedidoRestaurante
    extra = 0


@admin.register(PedidoRestaurante)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "origem", "mesa", "reserva", "total", "status", "metodo_pagamento", "estoque_baixado", "criado_em")
    inlines = [ItemInline]


@admin.register(MesaRestaurante)
class MesaAdmin(admin.ModelAdmin):
    list_display = ("numero", "codigo_qr", "estado")


@admin.register(MovimentoEstoqueRestaurante)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = ("criado_em", "produto", "tipo", "quantidade", "pedido")
    list_filter = ("tipo", "criado_em")
