from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from portal_cliente.utils import contexto_servicos_portal, obter_cliente
from usuarios.authz import cliente_required
from operacoes.models import Servico, SolicitacaoServico
from limpeza.models import PedidoLimpeza
from lavandaria.models import PedidoLavandaria
from restaurante.models import CategoriaProduto, ItemPedidoRestaurante, PedidoRestaurante, ProdutoRestaurante


@cliente_required
def home(request):
    cliente = obter_cliente(request)
    if not cliente:
        return render(
            request,
            "portal_cliente/sem_perfil.html",
            status=403,
        )
    return render(request, "portal_cliente/home.html", {"cliente": cliente})


@cliente_required
def minhas_reservas(request):
    cliente = obter_cliente(request)
    if not cliente:
        return redirect("portal_cliente:home")
    reservas = (
        cliente.reservas.select_related("unidade", "epoca")
        .filter(status__in=["confirmada", "ativa", "concluida"])
        .order_by("-id")
    )
    return render(
        request,
        "portal_cliente/reservas.html",
        {"cliente": cliente, "reservas": reservas},
    )


@cliente_required
def minhas_faturas(request):
    cliente = obter_cliente(request)
    if not cliente:
        return redirect("portal_cliente:home")
    from faturacao.models import Fatura

    faturas = Fatura.objects.filter(reserva__cliente=cliente).select_related("reserva")
    return render(
        request,
        "portal_cliente/faturas.html",
        {"cliente": cliente, "faturas": faturas},
    )


@cliente_required
def servicos(request):
    cliente = obter_cliente(request)
    if not cliente:
        return redirect("portal_cliente:home")
    ctx = contexto_servicos_portal(request)
    return render(
        request,
        "portal_cliente/servicos.html",
        {"cliente": cliente, **ctx},
    )


@cliente_required
def servico_limpeza(request):
    cliente = obter_cliente(request)
    if not cliente:
        return redirect("portal_cliente:home")
    ctx = contexto_servicos_portal(request)
    if not ctx.get("pode_solicitar_servicos"):
        messages.warning(request, "Os serviços ficam disponíveis apenas após o início da estadia.")
        return redirect("portal_cliente:servicos")

    reserva = ctx["reserva_servicos"]
    preco_diaria = Decimal("10000")
    dias = 1
    data_inicio = timezone.localdate()
    observacoes = ""
    total_estimado = preco_diaria

    if request.method == "POST":
        dias_raw = request.POST.get("dias", "1").strip()
        data_inicio_raw = request.POST.get("data_inicio", "").strip()
        observacoes = request.POST.get("observacoes", "").strip()
        try:
            dias = max(1, int(dias_raw))
        except (TypeError, ValueError):
            dias = 1
        try:
            data_inicio = timezone.datetime.strptime(data_inicio_raw, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            data_inicio = timezone.localdate()
        if data_inicio < reserva.data_inicio or data_inicio > reserva.data_fim:
            messages.error(request, "A data de início deve estar dentro do período da estadia ativa.")
        else:
            total_estimado = preco_diaria * dias
            with transaction.atomic():
                servico, _ = Servico.objects.get_or_create(
                    codigo="limpeza",
                    defaults={"nome": "Limpeza", "descricao": "Serviço de limpeza diária"},
                )
                SolicitacaoServico.objects.create(
                    reserva=reserva,
                    servico=servico,
                    descricao=f"Limpeza por {dias} dia(s) a partir de {data_inicio:%d/%m/%Y}. {observacoes}".strip(),
                )
                for i in range(dias):
                    pedido = PedidoLimpeza(
                        reserva=reserva,
                        data=data_inicio + timedelta(days=i),
                        tipo="normal",
                    )
                    pedido.save()
            messages.success(request, f"Solicitação de limpeza confirmada. Total estimado: Kz {total_estimado}.")
            return redirect("portal_cliente:servicos")
    else:
        if "reserva_servicos" in ctx:
            data_inicio = ctx["reserva_servicos"].data_inicio

    total_estimado = preco_diaria * dias
    return render(
        request,
        "portal_cliente/servico_limpeza.html",
        {
            "cliente": cliente,
            "reserva": reserva,
            "preco_diaria": preco_diaria,
            "dias": dias,
            "data_inicio": data_inicio,
            "observacoes": observacoes,
            "total_estimado": total_estimado,
        },
    )


LAVANDARIA_TABELA = [
    ("camisa", "Camisa", Decimal("2500")),
    ("blusa", "Blusa", Decimal("2500")),
    ("tshirt", "T-shirt", Decimal("2000")),
    ("calcao", "Calção", Decimal("2000")),
    ("calcas", "Calças", Decimal("3000")),
    ("saia", "Saia", Decimal("2500")),
    ("vestido_simples", "Vestido simples", Decimal("4000")),
    ("casaco_leve", "Casaco leve", Decimal("4500")),
    ("fato_completo", "Fato completo", Decimal("7500")),
    ("lencois", "Lençóis", Decimal("4000")),
    ("toalha", "Toalha", Decimal("2000")),
    ("edredao", "Edredão ou cobertor leve", Decimal("8000")),
]


@cliente_required
def servico_lavandaria(request):
    cliente = obter_cliente(request)
    if not cliente:
        return redirect("portal_cliente:home")
    ctx = contexto_servicos_portal(request)
    if not ctx.get("pode_solicitar_servicos"):
        messages.warning(request, "Este serviço só pode ser solicitado após reserva confirmada e check-in realizado.")
        return redirect("portal_cliente:servicos")

    reserva = ctx["reserva_servicos"]
    linhas = []
    total = Decimal("0")
    for codigo, nome, preco in LAVANDARIA_TABELA:
        qtd_raw = request.POST.get(f"qtd_{codigo}", "0") if request.method == "POST" else "0"
        try:
            qtd = max(0, int(qtd_raw))
        except (TypeError, ValueError):
            qtd = 0
        subtotal = preco * qtd
        total += subtotal
        linhas.append({"codigo": codigo, "nome": nome, "preco": preco, "qtd": qtd, "subtotal": subtotal})

    if request.method == "POST":
        if total <= 0:
            messages.error(request, "Indique pelo menos uma peça para solicitar lavandaria.")
        else:
            descricao = "; ".join([f"{l['nome']} x{l['qtd']}" for l in linhas if l["qtd"] > 0])
            with transaction.atomic():
                servico, _ = Servico.objects.get_or_create(
                    codigo="lavandaria",
                    defaults={"nome": "Lavandaria", "descricao": "Lavandaria por peça"},
                )
                SolicitacaoServico.objects.create(
                    reserva=reserva,
                    servico=servico,
                    descricao=f"Lavandaria: {descricao}",
                )
                PedidoLavandaria.objects.create(
                    reserva=reserva,
                    tipo="por_peca",
                    descricao=descricao,
                    preco_total=total,
                )
            messages.success(request, f"Pedido de lavandaria confirmado. Total: Kz {total}.")
            return redirect("portal_cliente:servicos")

    return render(
        request,
        "portal_cliente/servico_lavandaria.html",
        {"cliente": cliente, "reserva": reserva, "linhas": linhas, "total": total},
    )


MENU_BASE = {
    "Bebidas": [
        ("Água 50cl", Decimal("500")),
        ("Refrigerante lata", Decimal("800")),
        ("Sumo natural", Decimal("1500")),
        ("Cerveja nacional", Decimal("1200")),
    ],
    "Refeições": [
        ("Bitoque", Decimal("6500")),
        ("Frango grelhado com acompanhamento", Decimal("7500")),
        ("Peixe grelhado com acompanhamento", Decimal("8500")),
        ("Arroz com carne", Decimal("5500")),
        ("Arroz com frango", Decimal("5000")),
        ("Hambúrguer com batatas", Decimal("4500")),
        ("Omelete completa", Decimal("3500")),
        ("Sandes mista", Decimal("2500")),
    ],
    "Pequeno-almoço e extras": [
        ("Café", Decimal("700")),
        ("Chá", Decimal("600")),
        ("Leite", Decimal("800")),
        ("Pão com manteiga e ovo", Decimal("2000")),
        ("Pequeno-almoço simples", Decimal("3500")),
    ],
}


def _garantir_menu_base_restaurante():
    for idx, (categoria_nome, produtos) in enumerate(MENU_BASE.items(), start=1):
        categoria, _ = CategoriaProduto.objects.get_or_create(nome=categoria_nome, defaults={"ordem": idx})
        if categoria.ordem != idx:
            categoria.ordem = idx
            categoria.save(update_fields=["ordem"])
        for nome, preco in produtos:
            ProdutoRestaurante.objects.get_or_create(
                categoria=categoria,
                nome=nome,
                defaults={"preco": preco, "ativo": True},
            )


@cliente_required
def servico_restaurante(request):
    cliente = obter_cliente(request)
    if not cliente:
        return redirect("portal_cliente:home")
    ctx = contexto_servicos_portal(request)
    if not ctx.get("pode_solicitar_servicos"):
        messages.warning(request, "Os serviços ficam disponíveis apenas após o início da estadia.")
        return redirect("portal_cliente:servicos")
    reserva = ctx["reserva_servicos"]

    _garantir_menu_base_restaurante()
    produtos = ProdutoRestaurante.objects.filter(ativo=True).select_related("categoria").order_by("categoria__ordem", "nome")

    linhas = []
    total = Decimal("0")
    for p in produtos:
        qtd_raw = request.POST.get(f"qtd_{p.id}", "0") if request.method == "POST" else "0"
        try:
            qtd = max(0, int(qtd_raw))
        except (TypeError, ValueError):
            qtd = 0
        subtotal = (p.preco * Decimal(qtd)).quantize(Decimal("0.01"))
        total += subtotal
        linhas.append({"produto": p, "qtd": qtd, "subtotal": subtotal})

    if request.method == "POST":
        if total <= 0:
            messages.error(request, "Selecione pelo menos um produto para confirmar o pedido.")
        else:
            with transaction.atomic():
                servico, _ = Servico.objects.get_or_create(
                    codigo="restaurante",
                    defaults={"nome": "Restaurante", "descricao": "Pedido interno de restauração"},
                )
                descricao = "Pedido restaurante via área do cliente."
                SolicitacaoServico.objects.create(reserva=reserva, servico=servico, descricao=descricao)
                pedido = PedidoRestaurante.objects.create(reserva=reserva, status="pendente", total=Decimal("0.00"))
                for linha in linhas:
                    if linha["qtd"] > 0:
                        ItemPedidoRestaurante.objects.create(
                            pedido=pedido,
                            produto=linha["produto"],
                            quantidade=linha["qtd"],
                        )
                pedido.recalcular_total()
            messages.success(request, f"Pedido de restaurante confirmado. Total: Kz {total}.")
            return redirect("portal_cliente:servicos")

    categorias = {}
    for linha in linhas:
        categorias.setdefault(linha["produto"].categoria.nome, []).append(linha)
    return render(
        request,
        "portal_cliente/servico_restaurante.html",
        {"cliente": cliente, "reserva": reserva, "categorias": categorias, "total": total},
    )


def sem_acesso(request):
    return render(request, "portal_cliente/sem_acesso.html", status=403)
