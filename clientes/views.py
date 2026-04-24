from django.shortcuts import render

from clientes.models import Cliente
from usuarios.authz import interno_required


@interno_required
def lista(request):
    clientes = Cliente.objects.order_by("-id")[:100]
    return render(request, "clientes/lista.html", {"clientes": clientes})
