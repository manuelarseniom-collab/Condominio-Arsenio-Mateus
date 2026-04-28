from django.contrib import messages
from django.shortcuts import redirect, render

from usuarios.models import PerfilAcesso
from usuarios.perfil import get_perfil_atual


def home(request):
    perfil = get_perfil_atual(request)
    return render(request, "site_publico/home.html", {"role_publico": perfil})


def apartamentos(request):
    return render(request, "site_publico/apartamentos.html")


def disponibilidade(request):
    return render(request, "site_publico/apartamentos.html")


def servicos(request):
    return render(request, "site_publico/servicos.html")


def servicos_publicos(request):
    return render(request, "site_publico/servicos.html")


def solicitar_servico(request):
    messages.warning(
        request,
        "Este serviço só pode ser solicitado após reserva confirmada e check-in realizado.",
    )
    if not request.user.is_authenticated:
        return redirect("site_publico:servicos")
    role = getattr(getattr(request.user, "perfil_acesso", None), "role", PerfilAcesso.VISITANTE)
    if role == PerfilAcesso.CLIENTE_CONFIRMADO:
        return redirect("portal_cliente:servicos")
    return redirect("site_publico:servicos")


def restaurante(request):
    return render(request, "site_publico/restaurante.html")


def restaurante_publico(request):
    return render(request, "site_publico/restaurante.html")


def como_funciona(request):
    return render(request, "site_publico/faq.html")


def contactos(request):
    return render(request, "site_publico/contactos.html")


def faq(request):
    return render(request, "site_publico/faq.html")


def depoimentos(request):
    return render(request, "site_publico/depoimentos.html")
