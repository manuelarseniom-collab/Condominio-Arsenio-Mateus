from django.contrib import admin

from .models import CategoriaProduto, ItemPedidoRestaurante, PedidoRestaurante, ProdutoRestaurante


@admin.register(CategoriaProduto)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ordem")


@admin.register(ProdutoRestaurante)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "preco", "ativo")


class ItemInline(admin.TabularInline):
    model = ItemPedidoRestaurante
    extra = 0


@admin.register(PedidoRestaurante)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "reserva", "total", "status", "criado_em")
    inlines = [ItemInline]
