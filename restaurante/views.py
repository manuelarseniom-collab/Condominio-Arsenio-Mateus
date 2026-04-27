from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from faturacao.models import Fatura
from faturacao.services import add_item_fatura, recalcular_total_fatura
from reservas.models import Reserva
from restaurante.models import CategoriaProduto, ItemPedidoRestaurante, MesaRestaurante, PedidoRestaurante, ProdutoRestaurante
from usuarios.authz import interno_required
from usuarios.models import PerfilAcesso


@interno_required
def lista(request):
    _seed_menu_e_mesas()
    if not _user_pode_operar_restaurante(request.user):
        messages.error(request, "Acesso reservado ao trabalhador do restaurante.")
        return redirect("dashboard:home")

    if request.method == "POST":
        acao = request.POST.get("acao")
        if acao == "novo_presencial":
            pedido = _criar_pedido_presencial(request)
            if pedido:
                messages.success(request, f"Pedido presencial #{pedido.id} criado com sucesso.")
        elif acao == "atualizar_status":
            pedido_id = request.POST.get("pedido_id")
            novo_status = request.POST.get("status")
            pedido = get_object_or_404(PedidoRestaurante, pk=pedido_id)
            if novo_status in {s[0] for s in PedidoRestaurante.STATUS}:
                pedido.status = novo_status
                if novo_status == "pago":
                    pedido.pago_em = timezone.now()
                pedido.save(update_fields=["status", "pago_em"])
                messages.success(request, f"Pedido #{pedido.id} atualizado para {pedido.get_status_display()}.")
        elif acao == "gerar_fatura_pedido":
            pedido = get_object_or_404(PedidoRestaurante, pk=request.POST.get("pedido_id"))
            fatura = _gerar_fatura_do_pedido(pedido, request.user)
            messages.success(request, f"Fatura {fatura.numero_fatura} gerada para o pedido #{pedido.id}.")
            return redirect("faturacao:detalhe", fatura_id=fatura.id)
        return redirect("restaurante:lista")

    status = (request.GET.get("status") or "").strip()
    origem = (request.GET.get("origem") or "").strip()
    pedidos = PedidoRestaurante.objects.select_related("reserva", "mesa").order_by("-id")
    if status in {s[0] for s in PedidoRestaurante.STATUS}:
        pedidos = pedidos.filter(status=status)
    if origem in {o[0] for o in PedidoRestaurante.ORIGEM}:
        pedidos = pedidos.filter(origem=origem)

    hoje = timezone.localdate()
    total_dia = (
        PedidoRestaurante.objects.filter(criado_em__date=hoje, status__in=["entregue", "pago"]).aggregate(s=Sum("total"))["s"]
        or Decimal("0.00")
    )
    stats = {
        "recebido": PedidoRestaurante.objects.filter(status="recebido").count(),
        "em_preparacao": PedidoRestaurante.objects.filter(status="em_preparacao").count(),
        "pronto": PedidoRestaurante.objects.filter(status="pronto").count(),
        "entregue": PedidoRestaurante.objects.filter(status="entregue").count(),
        "cancelado": PedidoRestaurante.objects.filter(status="cancelado").count(),
        "quarto": PedidoRestaurante.objects.filter(origem="quarto").count(),
        "presencial": PedidoRestaurante.objects.filter(origem="presencial").count(),
        "mesa_qr": PedidoRestaurante.objects.filter(origem="mesa_qr").count(),
        "pendentes": PedidoRestaurante.objects.filter(status__in=["recebido", "aceite", "em_preparacao", "pronto"]).count(),
        "total_dia": total_dia,
    }

    produtos = ProdutoRestaurante.objects.filter(ativo=True, disponivel=True).select_related("categoria")
    mesas = MesaRestaurante.objects.all()
    pedidos_quarto = pedidos.filter(origem="quarto")[:40]
    pedidos_presenciais = pedidos.filter(origem="presencial")[:40]
    pedidos_qr = pedidos.filter(origem="mesa_qr")[:40]
    return render(
        request,
        "restaurante/dashboard.html",
        {
            "pedidos": pedidos[:80],
            "pedidos_quarto": pedidos_quarto,
            "pedidos_presenciais": pedidos_presenciais,
            "pedidos_qr": pedidos_qr,
            "produtos": produtos,
            "mesas": mesas,
            "status_ativo": status,
            "origem_ativa": origem,
            "stats": stats,
            "status_choices": PedidoRestaurante.STATUS,
            "origem_choices": PedidoRestaurante.ORIGEM,
        },
    )


@interno_required
def cozinha(request):
    if not _user_pode_operar_restaurante(request.user):
        messages.error(request, "Acesso reservado ao trabalhador do restaurante.")
        return redirect("dashboard:home")
    pedidos = PedidoRestaurante.objects.filter(status__in=["aceite", "em_preparacao", "pronto"]).select_related("mesa", "reserva")
    return render(request, "restaurante/cozinha.html", {"pedidos": pedidos})


def menu_qr(request, codigo_qr: str):
    _seed_menu_e_mesas()
    mesa = get_object_or_404(MesaRestaurante, codigo_qr=codigo_qr)
    produtos = ProdutoRestaurante.objects.filter(ativo=True, disponivel=True).select_related("categoria")
    if request.method == "POST":
        pedido = PedidoRestaurante.objects.create(
            origem="mesa_qr",
            mesa=mesa,
            status="recebido",
            cliente_nome=(request.POST.get("cliente_nome") or "").strip(),
            cliente_telefone=(request.POST.get("cliente_telefone") or "").strip(),
            qr_code_usado=codigo_qr,
        )
        for produto in produtos:
            qtd_raw = request.POST.get(f"qtd_{produto.id}", "0").strip()
            try:
                qtd = max(0, int(qtd_raw))
            except ValueError:
                qtd = 0
            if qtd > 0:
                ItemPedidoRestaurante.objects.create(pedido=pedido, produto=produto, quantidade=qtd)
        if pedido.itens.count() == 0:
            pedido.delete()
            messages.error(request, "Selecione pelo menos um produto para enviar o pedido.")
        else:
            pedido.recalcular_total()
            mesa.estado = "aguardando_atendimento"
            mesa.save(update_fields=["estado"])
            messages.success(request, f"Pedido Mesa {mesa.numero} enviado com sucesso.")
            return redirect("restaurante:menu_qr", codigo_qr=codigo_qr)
    categorias = {}
    for produto in produtos:
        categorias.setdefault(produto.categoria.nome, []).append(produto)
    return render(request, "restaurante/menu_qr.html", {"mesa": mesa, "categorias": categorias})


@interno_required
def relatorios(request):
    if not _user_pode_operar_restaurante(request.user):
        messages.error(request, "Acesso reservado ao trabalhador do restaurante.")
        return redirect("dashboard:home")
    periodo = (request.GET.get("periodo") or "hoje").strip()
    qs = PedidoRestaurante.objects.all()
    if periodo == "hoje":
        qs = qs.filter(criado_em__date=timezone.localdate())
    elif periodo == "7d":
        qs = qs.filter(criado_em__date__gte=timezone.localdate() - timedelta(days=7))
    elif periodo == "30d":
        qs = qs.filter(criado_em__date__gte=timezone.localdate() - timedelta(days=30))

    resumo = {
        "total_vendas": qs.filter(status__in=["entregue", "pago"]).aggregate(s=Sum("total"))["s"] or Decimal("0.00"),
        "cancelados": qs.filter(status="cancelado").count(),
        "por_estado": list(qs.values("status").annotate(total=Count("id")).order_by("status")),
        "por_origem": list(qs.values("origem").annotate(total=Count("id")).order_by("origem")),
        "por_mesa": list(qs.exclude(mesa__isnull=True).values("mesa__numero").annotate(total=Count("id")).order_by("mesa__numero")),
        "por_quarto": list(qs.exclude(reserva__isnull=True).values("reserva__unidade__codigo").annotate(total=Count("id")).order_by("reserva__unidade__codigo")),
    }
    return render(request, "restaurante/relatorios.html", {"resumo": resumo, "periodo": periodo})


def _user_pode_operar_restaurante(user) -> bool:
    role = getattr(getattr(user, "perfil_acesso", None), "role", "")
    return role in {
        PerfilAcesso.STAFF_RESTAURANTE,
        PerfilAcesso.RECEPCAO,
        PerfilAcesso.ADMIN,
        PerfilAcesso.ADMIN_CONDOMINIO,
        PerfilAcesso.ADMIN_SISTEMA,
    } or getattr(user, "is_superuser", False)


def _criar_pedido_presencial(request):
    mesa_id = request.POST.get("mesa_id")
    mesa = MesaRestaurante.objects.filter(pk=mesa_id).first() if mesa_id else None
    pedido = PedidoRestaurante.objects.create(
        origem="presencial",
        mesa=mesa,
        status="recebido",
        cliente_nome=(request.POST.get("cliente_nome") or "").strip(),
        cliente_telefone=(request.POST.get("cliente_telefone") or "").strip(),
        metodo_pagamento=(request.POST.get("metodo_pagamento") or "").strip(),
        observacoes=(request.POST.get("observacoes") or "").strip(),
    )
    produtos = ProdutoRestaurante.objects.filter(ativo=True, disponivel=True)
    for produto in produtos:
        qtd_raw = request.POST.get(f"qtd_{produto.id}", "0").strip()
        try:
            qtd = max(0, int(qtd_raw))
        except ValueError:
            qtd = 0
        if qtd > 0:
            ItemPedidoRestaurante.objects.create(pedido=pedido, produto=produto, quantidade=qtd)
    if pedido.itens.count() == 0:
        pedido.delete()
        messages.error(request, "Selecione pelo menos um item para criar o pedido presencial.")
        return None
    pedido.recalcular_total()
    if mesa:
        mesa.estado = "ocupada"
        mesa.save(update_fields=["estado"])
    return pedido


def _gerar_fatura_do_pedido(pedido, user):
    cliente_user = pedido.reserva.cliente.user if pedido.reserva_id and pedido.reserva.cliente.user_id else None
    fatura = Fatura.objects.create(
        cliente=cliente_user,
        reserva=pedido.reserva if pedido.reserva_id else None,
        tipo="servicos",
        estado_pagamento="validado" if pedido.metodo_pagamento else "pendente",
        metodo_pagamento=pedido.metodo_pagamento or "",
        emitido_por=user,
        observacoes=f"Conta restaurante do pedido #{pedido.id}. Pagamento prévio confirmado conforme política de reserva e serviços.",
    )
    for item in pedido.itens.select_related("produto"):
        add_item_fatura(
            fatura,
            f"{item.produto.nome} (Pedido restaurante #{pedido.id})",
            item.quantidade,
            item.produto.preco,
            origem_tipo="restaurante",
            origem_id=pedido.id,
            criado_por=user,
        )
    recalcular_total_fatura(fatura)
    if pedido.status == "pago":
        fatura.status = "paga"
        fatura.valor_pago = fatura.total
        fatura.estado_pagamento = "validado"
        fatura.save(update_fields=["status", "valor_pago", "estado_pagamento", "valor_pendente"])
    return fatura


def _seed_menu_e_mesas():
    categorias = {
        "Bebidas": [
            ("Água 50cl", "Água mineral 50cl", Decimal("500")),
            ("Refrigerante lata", "Lata 33cl", Decimal("800")),
            ("Sumo natural", "Copo de sumo natural", Decimal("1500")),
            ("Cerveja nacional", "Cerveja nacional", Decimal("1200")),
            ("Café", "Café expresso", Decimal("700")),
            ("Chá", "Chá simples", Decimal("600")),
        ],
        "Pequeno-almoço": [
            ("Pão com manteiga e ovo", "Pequeno-almoço simples", Decimal("2000")),
            ("Pequeno-almoço simples", "Café/Chá e pão", Decimal("3500")),
            ("Pequeno-almoço completo", "Pequeno-almoço reforçado", Decimal("5000")),
        ],
        "Refeições": [
            ("Bitoque", "Prato principal", Decimal("6500")),
            ("Frango grelhado com acompanhamento", "Prato principal", Decimal("7500")),
            ("Peixe grelhado com acompanhamento", "Prato principal", Decimal("8500")),
            ("Arroz com carne", "Prato principal", Decimal("5500")),
            ("Arroz com frango", "Prato principal", Decimal("5000")),
            ("Hambúrguer com batatas", "Prato rápido", Decimal("4500")),
            ("Omelete completa", "Prato rápido", Decimal("3500")),
            ("Sandes mista", "Prato rápido", Decimal("2500")),
        ],
        "Sobremesas": [
            ("Mousse de chocolate", "Sobremesa do dia", Decimal("2200")),
            ("Salada de frutas", "Sobremesa fresca", Decimal("1800")),
        ],
        "Extras": [
            ("Gelo extra", "Complemento", Decimal("300")),
            ("Molho especial", "Complemento", Decimal("500")),
        ],
    }
    for ordem, (nome_cat, produtos) in enumerate(categorias.items(), start=1):
        categoria, _ = CategoriaProduto.objects.get_or_create(nome=nome_cat, defaults={"ordem": ordem})
        if categoria.ordem != ordem:
            categoria.ordem = ordem
            categoria.save(update_fields=["ordem"])
        for nome, descricao, preco in produtos:
            ProdutoRestaurante.objects.get_or_create(
                categoria=categoria,
                nome=nome,
                defaults={
                    "descricao": descricao,
                    "preco": preco,
                    "ativo": True,
                    "disponivel": True,
                    "tempo_preparo_min": 15,
                },
            )
    for n in range(1, 11):
        MesaRestaurante.objects.get_or_create(numero=n, defaults={"codigo_qr": f"MESA-{n:02d}"})
