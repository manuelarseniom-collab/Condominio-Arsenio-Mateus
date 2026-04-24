from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from usuarios.authz import administrador_required, trabalhador_required

from .models import AtribuicaoStaff, SolicitacaoServico


@trabalhador_required
def painel_staff(request):
    role = request.user.perfil_acesso.role
    area = role.replace("staff_", "")
    estado = request.GET.get("estado")
    apartamento = request.GET.get("apartamento")

    tarefas = AtribuicaoStaff.objects.select_related("solicitacao__reserva__unidade", "staff").filter(
        area=area
    )
    if estado:
        tarefas = tarefas.filter(solicitacao__status=estado)
    if apartamento:
        tarefas = tarefas.filter(solicitacao__reserva__unidade__codigo__icontains=apartamento)
    return render(
        request,
        "operacoes/painel_staff.html",
        {"tarefas": tarefas[:100], "area": area, "estado": estado, "apartamento": apartamento},
    )


@login_required
def historico_solicitacoes_cliente(request):
    if not hasattr(request.user, "perfil_cliente"):
        return render(request, "portal_cliente/sem_perfil.html", status=403)
    cliente = request.user.perfil_cliente
    solicitacoes = SolicitacaoServico.objects.select_related("servico", "reserva__unidade").filter(
        reserva__cliente=cliente
    )
    return render(
        request,
        "portal_cliente/historico_solicitacoes.html",
        {"solicitacoes": solicitacoes[:100]},
    )


@administrador_required
def painel_admin_operacional(request):
    q = request.GET.get("q", "")
    reservas_qs = SolicitacaoServico.objects.select_related("reserva__cliente", "servico")
    if q:
        reservas_qs = reservas_qs.filter(
            Q(reserva__cliente__nome__icontains=q)
            | Q(reserva__unidade__codigo__icontains=q)
            | Q(servico__nome__icontains=q)
        )
    return render(request, "operacoes/painel_admin.html", {"solicitacoes": reservas_qs[:150], "q": q})
