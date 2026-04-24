from django.shortcuts import render

from restaurante.models import PedidoRestaurante, ProdutoRestaurante
from usuarios.authz import interno_required


@interno_required
def lista(request):
    pedidos = PedidoRestaurante.objects.select_related("reserva").order_by("-id")[:40]
    produtos = ProdutoRestaurante.objects.filter(ativo=True).select_related("categoria")
    return render(
        request,
        "restaurante/lista.html",
        {"pedidos": pedidos, "produtos": produtos},
    )
