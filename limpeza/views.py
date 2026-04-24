from django.shortcuts import render

from limpeza.models import PedidoLimpeza
from usuarios.authz import interno_required


@interno_required
def lista(request):
    pedidos = PedidoLimpeza.objects.select_related("reserva").order_by("-id")[:50]
    return render(request, "limpeza/lista.html", {"pedidos": pedidos})
