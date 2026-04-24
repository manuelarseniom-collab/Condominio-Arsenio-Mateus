from django.shortcuts import render

from lavandaria.models import PedidoLavandaria
from usuarios.authz import interno_required


@interno_required
def lista(request):
    pedidos = PedidoLavandaria.objects.select_related("reserva").order_by("-id")[:50]
    return render(request, "lavandaria/lista.html", {"pedidos": pedidos})
