from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.roles import ROLES_ADMIN, get_user_role

from .forms import DepoimentoForm
from .models import Depoimento
from .services import cliente_pode_deixar_depoimento, reserva_elegivel_para_depoimento


def depoimentos_publicos(request):
    depoimentos = Depoimento.objects.filter(
        status="aprovado",
        publicado=True,
        abusivo=False,
    ).select_related("user")
    return render(
        request,
        "depoimentos/depoimentos.html",
        {
            "depoimentos": depoimentos,
        },
    )


@login_required
def criar_depoimento(request):
    if not cliente_pode_deixar_depoimento(request.user):
        messages.warning(
            request,
            "Para deixar um depoimento, é necessário ter uma reserva ativa ou concluída.",
        )
        return redirect("site_publico:depoimentos")

    reserva = reserva_elegivel_para_depoimento(request.user)
    if not reserva:
        messages.warning(
            request,
            "Só é possível deixar depoimento após uma estadia ativa ou concluída.",
        )
        return redirect("site_publico:depoimentos")

    if Depoimento.objects.filter(user=request.user, reserva=reserva).exists():
        messages.info(request, "Já existe um depoimento associado a esta estadia.")
        return redirect("site_publico:depoimentos")

    if request.method == "POST":
        form = DepoimentoForm(request.POST)
        if form.is_valid():
            depoimento = form.save(commit=False)
            depoimento.user = request.user
            depoimento.reserva = reserva
            depoimento.status = "pendente"
            depoimento.publicado = False
            depoimento.abusivo = False
            depoimento.save()
            messages.success(
                request,
                "O seu depoimento foi enviado e ficará visível após validação da administração.",
            )
            return redirect("site_publico:depoimentos")
    else:
        form = DepoimentoForm()

    return render(
        request,
        "depoimentos/criar_depoimento.html",
        {
            "form": form,
            "reserva": reserva,
        },
    )


@login_required
def admin_depoimentos(request):
    role = get_user_role(request.user)
    if not (request.user.is_superuser or role in ROLES_ADMIN):
        messages.error(request, "Acesso não autorizado para este perfil.")
        return redirect("usuarios:acesso_interno")

    if request.method == "POST":
        depoimento_id = request.POST.get("depoimento_id")
        acao = request.POST.get("acao")
        motivo = (request.POST.get("motivo_moderacao") or "").strip()
        depoimento = get_object_or_404(Depoimento, pk=depoimento_id)

        if acao == "aprovar":
            depoimento.status = "aprovado"
            depoimento.publicado = True
            depoimento.abusivo = False
            if motivo:
                depoimento.motivo_moderacao = motivo
            depoimento.save()
            messages.success(request, "Depoimento aprovado e publicado.")
        elif acao == "rejeitar":
            depoimento.status = "rejeitado"
            depoimento.publicado = False
            depoimento.motivo_moderacao = motivo or depoimento.motivo_moderacao
            depoimento.save()
            messages.warning(request, "Depoimento rejeitado.")
        elif acao == "ocultar":
            depoimento.status = "oculto"
            depoimento.publicado = False
            depoimento.motivo_moderacao = motivo or depoimento.motivo_moderacao
            depoimento.save()
            messages.warning(request, "Depoimento ocultado.")
        elif acao == "abusivo":
            depoimento.status = "rejeitado"
            depoimento.publicado = False
            depoimento.abusivo = True
            depoimento.motivo_moderacao = motivo or "Depoimento removido por violar as regras de publicação."
            depoimento.save()
            messages.error(request, "Depoimento marcado como abusivo e removido da publicação.")
        elif acao == "apagar":
            depoimento.delete()
            messages.error(request, "Depoimento apagado definitivamente.")

        return redirect("site_publico:admin_depoimentos")

    status_filtro = (request.GET.get("status") or "").strip()
    abusivo_filtro = (request.GET.get("abusivo") or "").strip()
    depoimentos = Depoimento.objects.select_related("user", "reserva").all()
    if status_filtro in {"pendente", "aprovado", "rejeitado", "oculto"}:
        depoimentos = depoimentos.filter(status=status_filtro)
    if abusivo_filtro in {"sim", "nao"}:
        depoimentos = depoimentos.filter(abusivo=(abusivo_filtro == "sim"))

    total = Depoimento.objects.count()
    pendentes = Depoimento.objects.filter(status="pendente").count()
    aprovados = Depoimento.objects.filter(status="aprovado").count()
    rejeitados = Depoimento.objects.filter(status="rejeitado").count()
    ocultos = Depoimento.objects.filter(status="oculto").count()
    abusivos = Depoimento.objects.filter(abusivo=True).count()
    return render(
        request,
        "depoimentos/admin_depoimentos.html",
        {
            "depoimentos": depoimentos,
            "filtro_status": status_filtro,
            "filtro_abusivo": abusivo_filtro,
            "totais": {
                "total": total,
                "pendentes": pendentes,
                "aprovados": aprovados,
                "rejeitados": rejeitados,
                "ocultos": ocultos,
                "abusivos": abusivos,
            },
        },
    )
