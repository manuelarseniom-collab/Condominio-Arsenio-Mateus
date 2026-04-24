from django.shortcuts import render

from unidades.models import Unidade
from usuarios.authz import administrador_required


@administrador_required
def lista(request):
    unidades = Unidade.objects.order_by("andar", "codigo")
    return render(request, "unidades/lista.html", {"unidades": unidades})
