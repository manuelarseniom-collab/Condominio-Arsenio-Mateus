from datetime import timedelta

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from clientes.models import Cliente
from operacoes.models import SolicitacaoServico
from reservas.models import Reserva
from faturacao.models import Pagamento
from usuarios.authz import interno_required
from usuarios.roles import get_user_profile, get_user_role, profile_display_name, role_display_name

@interno_required
def home(request):
    if request.method == "POST":
        reserva_id = request.POST.get("reserva_id")
        if reserva_id and request.POST.get("confirmar_whatsapp") == "1":
            reserva = get_object_or_404(Reserva.objects.select_related("cliente"), pk=reserva_id)
            reserva.pagamento_confirmado_whatsapp = True
            reserva.save(update_fields=["pagamento_confirmado_whatsapp", "status"])
            messages.success(request, f"Pagamento da reserva #{reserva.id} confirmado por WhatsApp.")
        return redirect("dashboard:home")

    role = get_user_role(request.user)
    profile = get_user_profile(request.user)
    hoje = timezone.localdate()

    reservas_qs = Reserva.objects.all()
    solicitacoes_qs = SolicitacaoServico.objects.all()
    pagamentos_qs = Pagamento.objects.all()
    clientes_qs = Cliente.objects.all()

    contexto = {
        "role_atual": role,
        "role_atual_label": role_display_name(role),
        "perfil_atual": profile,
        "perfil_atual_label": profile_display_name(profile),
        "clientes_total": clientes_qs.count(),
        "clientes_ativos": clientes_qs.filter(estado="ativo").count(),
        "clientes_inativos": clientes_qs.filter(estado="inativo").count(),
        "financeiro_por_pagar": clientes_qs.filter(situacao_financeira="por_pagar").count(),
        "financeiro_validacao": clientes_qs.filter(situacao_financeira="em_validacao").count(),
        "financeiro_pago": clientes_qs.filter(situacao_financeira="paga").count(),
        "clientes_lista": clientes_qs.order_by("-id")[:15],
        "reservas_ativas_lista": reservas_qs.filter(status="ativa").select_related("cliente", "unidade").order_by("-id")[:15],
        "reservas_pendentes_lista": reservas_qs.filter(
            status__in=["pendente", "pre_reserva", "aguardando_pagamento", "pagamento_em_validacao", "aguardando_confirmacao"]
        ).select_related("cliente", "unidade").order_by("-id")[:15],
        "reservas_por_estado": {
            "ativas": reservas_qs.filter(status="ativa").count(),
            "pendentes": reservas_qs.filter(
                status__in=["pendente", "pre_reserva", "aguardando_pagamento", "pagamento_em_validacao", "aguardando_confirmacao"]
            ).count(),
            "confirmadas": reservas_qs.filter(status="confirmada").count(),
            "canceladas": reservas_qs.filter(status="cancelada").count(),
            "concluidas": reservas_qs.filter(status="concluida").count(),
        },
        "reservas_whatsapp_pendentes": reservas_qs.filter(
            pagamento_confirmado_whatsapp=False,
            status__in=["pendente", "pre_reserva", "aguardando_pagamento", "pagamento_em_validacao", "aguardando_confirmacao"],
        ).select_related("cliente", "unidade").order_by("-id")[:10],
        "reservas_pendentes": reservas_qs.filter(
            status__in=["pre_reserva", "aguardando_pagamento", "pagamento_em_validacao", "aguardando_confirmacao"]
        ).count(),
        "reservas_confirmadas": reservas_qs.filter(status="confirmada").count(),
        "reservas_ativas": reservas_qs.filter(status="ativa").count(),
        "servicos_abertos": solicitacoes_qs.exclude(status__in=["concluido", "cancelado"]).count(),
        "servicos_concluidos": solicitacoes_qs.filter(status="concluido").count(),
        "pedidos_urgentes": solicitacoes_qs.filter(
            status__in=["solicitado", "atribuido"],
            criado_em__lt=timezone.now() - timedelta(hours=24),
        ).count(),
        "atividade_hoje": solicitacoes_qs.filter(criado_em__date=hoje).count(),
        "atividade_recente": solicitacoes_qs.select_related("servico", "reserva__unidade").order_by("-criado_em")[:6],
        "pagamentos_hoje": pagamentos_qs.filter(data__date=hoje).count(),
        "reservas_canceladas": reservas_qs.filter(status="cancelada").count(),
        "checkins_hoje": reservas_qs.filter(data_inicio=hoje, status__in=["ativa", "confirmada"]).count(),
        "checkouts_hoje": reservas_qs.filter(data_fim=hoje, status__in=["ativa", "concluida"]).count(),
    }
    return render(request, "dashboard/home.html", contexto)
