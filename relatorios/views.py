from django.shortcuts import render
from usuarios.authz import administrador_required


@administrador_required
def lista(request):
    return render(request, "relatorios/lista.html")
