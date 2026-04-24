from django.shortcuts import render

from faturacao.models import Fatura
from usuarios.authz import interno_required


@interno_required
def lista(request):
    faturas = Fatura.objects.select_related("reserva", "reserva__cliente").order_by("-id")[:50]
    return render(
        request,
        "faturacao/lista.html",
        {"faturas": faturas},
    )
