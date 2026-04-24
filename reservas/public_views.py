"""
Vistas públicas: pesquisa de disponibilidade e pré-reserva por unidade real.
"""

from datetime import date
import logging

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from clientes.models import Cliente
from faturacao.services import (
    criar_fatura_base_para_reserva,
    obter_fatura_principal_reserva,
    recalcular_total_fatura,
)
from reservas.disponibilidade import apartamentos_disponiveis, unidade_disponivel_no_periodo
from reservas.forms_public import BuscaDisponibilidadeForm, IniciarPreReservaForm
from reservas.models import Reserva
from reservas.referencia_pagamento import gerar_referencia_pagamento
from unidades.models import Unidade

logger = logging.getLogger(__name__)


def buscar_apartamentos(request):
    """Pesquisa de disponibilidade por período e filtros."""
    hoje = timezone.localdate().isoformat()
    resultados = None
    datas_busca = None
    pesquisado = False

    get_initial = {}
    tipo_legacy = (request.GET.get("tipo") or request.GET.get("tipologia") or "").strip().upper()
    if tipo_legacy in ("T0", "T1", "T2", "T3", "PENTHOUSE", "MASTER"):
        get_initial["tipologia"] = "PENTHOUSE" if tipo_legacy == "MASTER" else tipo_legacy

    filtros_presentes = any(
        request.GET.get(k)
        for k in ("data_checkin", "data_checkout", "tipologia", "andar")
    )
    if request.GET.get("pesquisar") or filtros_presentes:
        pesquisado = True
        form = BuscaDisponibilidadeForm(request.GET)
        if form.is_valid():
            di = form.cleaned_data["data_checkin"]
            df = form.cleaned_data["data_checkout"]
            tip = form.cleaned_data.get("tipologia") or None
            andar = form.cleaned_data.get("andar")
            resultados = apartamentos_disponiveis(
                di,
                df,
                tipologia=tip,
                andar=andar if andar is not None else None,
            )
            datas_busca = {"checkin": di, "checkout": df}
    else:
        form = BuscaDisponibilidadeForm(initial=get_initial)

    form.fields["data_checkin"].widget.attrs["min"] = hoje
    form.fields["data_checkout"].widget.attrs["min"] = hoje

    return render(
        request,
        "reservas/buscar_apartamentos.html",
        {
            "form": form,
            "resultados": resultados,
            "pesquisado": pesquisado,
            "hoje": hoje,
            "datas_busca": datas_busca,
        },
    )


def iniciar_pre_reserva(request, apartment_id: int):
    """Pré-reserva apenas após escolha de unidade específica disponível."""
    unidade = get_object_or_404(Unidade, pk=apartment_id, disponivel=True)
    hoje = timezone.localdate().isoformat()

    di_ini = request.GET.get("checkin") or request.GET.get("data_checkin")
    df_ini = request.GET.get("checkout") or request.GET.get("data_checkout")
    initial = {}
    aviso_periodo_get = None
    if di_ini and df_ini:
        try:
            di0 = date.fromisoformat(di_ini)
            df0 = date.fromisoformat(df_ini)
            initial["data_checkin"] = di_ini
            initial["data_checkout"] = df_ini
            if di0 >= df0:
                aviso_periodo_get = "Datas inválidas na ligação. Escolha novamente o período na pesquisa."
            elif not unidade_disponivel_no_periodo(unidade.pk, di0, df0):
                aviso_periodo_get = (
                    "Este apartamento já não está disponível no período indicado. "
                    "Volte à pesquisa de disponibilidade."
                )
        except ValueError:
            aviso_periodo_get = "Datas inválidas. Utilize a pesquisa de disponibilidade."

    if request.method == "POST":
        form = IniciarPreReservaForm(request.POST)
        form.fields["data_checkin"].widget.attrs["min"] = hoje
        form.fields["data_checkout"].widget.attrs["min"] = hoje
        if form.is_valid():
            logger.info("form válido")
            di = form.cleaned_data["data_checkin"]
            df = form.cleaned_data["data_checkout"]
            email = form.cleaned_data["email"].strip().lower()

            if not unidade_disponivel_no_periodo(unidade.pk, di, df):
                form.add_error(
                    None,
                    "Este apartamento já não está disponível nas datas escolhidas. Volte à pesquisa e escolha outra unidade ou período.",
                )
            else:
                try:
                    with transaction.atomic():
                        cliente, _ = Cliente.objects.get_or_create(
                            email=email,
                            defaults={
                                "nome": form.cleaned_data["nome_cliente"],
                                "telefone": form.cleaned_data["telefone"],
                                "email": email,
                            },
                        )
                        cliente.nome = form.cleaned_data["nome_cliente"]
                        cliente.telefone = form.cleaned_data["telefone"]
                        cliente.email = email
                        cliente.nacionalidade = form.cleaned_data["nacionalidade"]
                        cliente.tipo_documento = form.cleaned_data["tipo_documento"]
                        cliente.numero_documento_identificacao = form.cleaned_data["numero_documento_identificacao"]
                        cliente.data_nascimento = form.cleaned_data["data_nascimento"]
                        cliente.morada = form.cleaned_data.get("morada") or ""
                        cliente.cidade = form.cleaned_data.get("cidade") or ""
                        cliente.pais_residencia = form.cleaned_data.get("pais_residencia") or ""
                        cliente.empresa_instituicao = form.cleaned_data.get("empresa_instituicao") or ""
                        cliente.contacto_alternativo = form.cleaned_data.get("contacto_alternativo") or ""
                        cliente.preferencia_contacto = form.cleaned_data.get("preferencia_contacto") or ""
                        cliente.save()

                        reserva = (
                            Reserva.objects.filter(
                                cliente=cliente,
                                unidade=unidade,
                                data_inicio=di,
                                data_fim=df,
                                status__in=("aguardando_pagamento", "pagamento_em_validacao", "pre_reserva"),
                            )
                            .order_by("-id")
                            .first()
                        )
                        if reserva:
                            logger.info("reserva existente reutilizada com id %s", reserva.pk)
                            reserva.status = "aguardando_pagamento"
                            reserva.nome_completo = form.cleaned_data["nome_cliente"]
                            reserva.telefone = form.cleaned_data["telefone"]
                            reserva.email = email
                            reserva.nacionalidade = form.cleaned_data["nacionalidade"]
                            reserva.tipo_documento = form.cleaned_data["tipo_documento"]
                            reserva.numero_documento_identificacao = form.cleaned_data["numero_documento_identificacao"]
                            reserva.data_nascimento = form.cleaned_data["data_nascimento"]
                            reserva.morada = form.cleaned_data.get("morada") or ""
                            reserva.cidade = form.cleaned_data.get("cidade") or ""
                            reserva.pais_residencia = form.cleaned_data.get("pais_residencia") or ""
                            reserva.contacto_alternativo = form.cleaned_data.get("contacto_alternativo") or ""
                            reserva.preferencia_contacto = form.cleaned_data.get("preferencia_contacto") or ""
                            reserva.numero_hospedes = form.cleaned_data["numero_hospedes"]
                            reserva.finalidade_estadia = form.cleaned_data["finalidade_estadia"]
                            reserva.observacoes = (form.cleaned_data.get("observacoes") or "").strip()
                            reserva.pedido_especial = (form.cleaned_data.get("pedido_especial") or "").strip()
                            reserva.save()
                            logger.info("reserva atualizada com id %s", reserva.pk)
                        else:
                            reserva = Reserva(
                                cliente=cliente,
                                unidade=unidade,
                                data_inicio=di,
                                data_fim=df,
                                status="aguardando_pagamento",
                                nome_completo=form.cleaned_data["nome_cliente"],
                                telefone=form.cleaned_data["telefone"],
                                email=email,
                                nacionalidade=form.cleaned_data["nacionalidade"],
                                tipo_documento=form.cleaned_data["tipo_documento"],
                                numero_documento_identificacao=form.cleaned_data["numero_documento_identificacao"],
                                data_nascimento=form.cleaned_data["data_nascimento"],
                                morada=form.cleaned_data.get("morada") or "",
                                cidade=form.cleaned_data.get("cidade") or "",
                                pais_residencia=form.cleaned_data.get("pais_residencia") or "",
                                contacto_alternativo=form.cleaned_data.get("contacto_alternativo") or "",
                                preferencia_contacto=form.cleaned_data.get("preferencia_contacto") or "",
                                numero_hospedes=form.cleaned_data["numero_hospedes"],
                                finalidade_estadia=form.cleaned_data["finalidade_estadia"],
                                observacoes=(form.cleaned_data.get("observacoes") or "").strip(),
                                pedido_especial=(form.cleaned_data.get("pedido_especial") or "").strip(),
                            )
                            reserva.save()
                            logger.info("reserva criada com id %s", reserva.pk)

                        if not reserva.pagamento_entidade or not reserva.pagamento_referencia:
                            ent, ref = gerar_referencia_pagamento(reserva)
                            reserva.pagamento_entidade = ent
                            reserva.pagamento_referencia = ref
                            reserva.save(update_fields=["pagamento_entidade", "pagamento_referencia"])

                        criar_fatura_base_para_reserva(reserva)
                        fatura = obter_fatura_principal_reserva(reserva)
                        if not fatura:
                            raise ValueError("Não foi possível criar a fatura da reserva.")
                        recalcular_total_fatura(fatura)
                        pagamento, _ = fatura.pagamentos.get_or_create(
                            status="pendente",
                            metodo="referencia_bancaria",
                            defaults={"valor": fatura.total},
                        )
                        if pagamento.valor != fatura.total:
                            pagamento.valor = fatura.total
                            pagamento.save(update_fields=["valor"])
                        logger.info("pagamento salvo com id %s", pagamento.pk)
                except Exception as exc:
                    messages.error(request, f"Não foi possível concluir a pré-reserva: {exc}")
                    logger.exception("erro ao persistir pré-reserva")
                else:
                    request.session["pre_reserva_concluida_id"] = reserva.pk
                    logger.info("redirect para pre_reserva_sucesso (id %s)", reserva.pk)
                    messages.success(
                        request,
                        "Pré-reserva guardada com sucesso. Utilize a referência para concluir o pagamento.",
                    )
                    return redirect("site_publico:pre_reserva_sucesso")
        else:
            logger.warning("form inválido: %s", form.errors.as_json())
    else:
        form = IniciarPreReservaForm(initial=initial)
        form.fields["data_checkin"].widget.attrs["min"] = hoje
        form.fields["data_checkout"].widget.attrs["min"] = hoje

    return render(
        request,
        "reservas/iniciar_pre_reserva.html",
        {
            "form": form,
            "unidade": unidade,
            "numero_quartos": unidade.numero_quartos_efetivo,
            "aviso_periodo_get": aviso_periodo_get,
        },
    )
