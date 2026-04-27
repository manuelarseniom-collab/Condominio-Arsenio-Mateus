from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

from usuarios.forms import SecureAuthenticationForm
from usuarios.models import PerfilAcesso
from reservas.models import Reserva
from limpeza.models import PedidoLimpeza
from lavandaria.models import PedidoLavandaria
from restaurante.models import PedidoRestaurante, ProdutoRestaurante
from faturacao.models import Pagamento


def _normalizar_role(role: str) -> str:
    return {
        "recepcionista": PerfilAcesso.RECEPCAO,
        "trabalhador_reservas": PerfilAcesso.RECEPCAO,
        "restaurante": PerfilAcesso.STAFF_RESTAURANTE,
        "trabalhador_restaurante": PerfilAcesso.STAFF_RESTAURANTE,
        "servicos": PerfilAcesso.STAFF_MANUTENCAO,
        "trabalhador_servicos": PerfilAcesso.STAFF_MANUTENCAO,
        "trabalhador_limpeza": PerfilAcesso.STAFF_LIMPEZA,
        "trabalhador_lavandaria": PerfilAcesso.STAFF_LAVANDARIA,
        "admin_condominio": PerfilAcesso.ADMIN_CONDOMINIO,
        "admin_sistema": PerfilAcesso.ADMIN_SISTEMA,
    }.get(role, role)


def redirecionar_pos_login_interno(user) -> str:
    if user.is_superuser:
        return "usuarios:acesso_interno"

    role = getattr(getattr(user, "perfil_acesso", None), "role", PerfilAcesso.VISITANTE)
    role = _normalizar_role(role)

    if role == PerfilAcesso.STAFF_RESTAURANTE:
        return "usuarios:dashboard_restaurante"
    if role in {PerfilAcesso.STAFF_MANUTENCAO, PerfilAcesso.STAFF_LIMPEZA, PerfilAcesso.STAFF_LAVANDARIA}:
        return "usuarios:dashboard_servicos"
    if role == PerfilAcesso.RECEPCAO:
        return "usuarios:dashboard_reservas"
    if role in {PerfilAcesso.ADMIN, PerfilAcesso.ADMIN_CONDOMINIO, PerfilAcesso.ADMIN_SISTEMA}:
        return "usuarios:acesso_interno"
    return "usuarios:acesso_interno"


@method_decorator(never_cache, name="dispatch")
class UsuarioLoginView(LoginView):
    template_name = "usuarios/login.html"
    redirect_authenticated_user = False
    authentication_form = SecureAuthenticationForm

    def form_valid(self, form):
        # Evita herdar estado de sessão anterior ao trocar de conta/perfil.
        if self.request.user.is_authenticated:
            logout(self.request)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Credenciais inválidas. Verifique os dados e tente novamente.",
        )
        return super().form_invalid(form)

    def get_success_url(self):
        role = PerfilAcesso.VISITANTE
        if hasattr(self.request.user, "perfil_acesso"):
            role = self.request.user.perfil_acesso.role
        if role in (
            PerfilAcesso.ADMIN,
            PerfilAcesso.ADMIN_CONDOMINIO,
            PerfilAcesso.ADMIN_SISTEMA,
            PerfilAcesso.RECEPCAO,
            PerfilAcesso.STAFF_LAVANDARIA,
            PerfilAcesso.STAFF_LIMPEZA,
            PerfilAcesso.STAFF_MANUTENCAO,
            PerfilAcesso.STAFF_RESTAURANTE,
        ):
            return reverse("dashboard:home")
        if role == PerfilAcesso.CLIENTE_CONFIRMADO:
            return reverse("portal_cliente:home")
        return reverse("site_publico:home")


@method_decorator(never_cache, name="dispatch")
class UsuarioLogoutView(LogoutView):
    http_method_names = ["post", "options"]
    next_page = reverse_lazy("site_publico:home")

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        request.session.flush()
        return response


class LoginClienteView(UsuarioLoginView):
    template_name = "usuarios/login_cliente.html"
    extra_context = {
        "area_titulo": "Área do cliente",
        "area_subtitulo": "Disponível apenas para clientes com reserva confirmada e conta ativada.",
    }

    def form_valid(self, form):
        response = super().form_valid(form)
        role = getattr(getattr(self.request.user, "perfil_acesso", None), "role", PerfilAcesso.VISITANTE)
        if role in (
            PerfilAcesso.CLIENTE_CONFIRMADO,
            PerfilAcesso.ADMIN,
            PerfilAcesso.ADMIN_CONDOMINIO,
            PerfilAcesso.ADMIN_SISTEMA,
        ) or self.request.user.is_superuser:
            return response
        messages.error(
            self.request,
            "Área do cliente disponível apenas após confirmação da reserva.",
        )
        return redirect("usuarios:entrar")


class LoginStaffView(UsuarioLoginView):
    template_name = "usuarios/login_staff.html"
    extra_context = {
        "area_titulo": "Área do trabalhador",
        "area_subtitulo": "Acesso interno para receção e operadores autorizados pelo administrador.",
    }
    
    def form_valid(self, form):
        super().form_valid(form)
        role = getattr(getattr(self.request.user, "perfil_acesso", None), "role", PerfilAcesso.VISITANTE)
        role = _normalizar_role(role)
        if role in (
            PerfilAcesso.RECEPCAO,
            PerfilAcesso.STAFF_LAVANDARIA,
            PerfilAcesso.STAFF_LIMPEZA,
            PerfilAcesso.STAFF_MANUTENCAO,
            PerfilAcesso.STAFF_RESTAURANTE,
            PerfilAcesso.ADMIN,
            PerfilAcesso.ADMIN_CONDOMINIO,
            PerfilAcesso.ADMIN_SISTEMA,
        ) or self.request.user.is_superuser:
            destino = redirecionar_pos_login_interno(self.request.user)
            if destino == "usuarios:acesso_interno" and role == PerfilAcesso.VISITANTE:
                messages.warning(self.request, "Perfil interno não reconhecido. Verifique as permissões.")
            return redirect(destino)
        messages.error(
            self.request,
            "Credenciais sem acesso à área de trabalhador.",
        )
        return redirect("usuarios:entrar")


class LoginAdminView(UsuarioLoginView):
    template_name = "usuarios/login_admin.html"
    extra_context = {
        "area_titulo": "Administração",
        "area_subtitulo": "Acesso reservado à administração do sistema e do condomínio.",
    }

    def form_valid(self, form):
        response = super().form_valid(form)
        role = getattr(getattr(self.request.user, "perfil_acesso", None), "role", PerfilAcesso.VISITANTE)
        if role in (
            PerfilAcesso.ADMIN,
            PerfilAcesso.ADMIN_CONDOMINIO,
            PerfilAcesso.ADMIN_SISTEMA,
        ) or self.request.user.is_superuser:
            return response
        messages.error(
            self.request,
            "Credenciais sem acesso à administração.",
        )
        return redirect("usuarios:acesso_interno")


@never_cache
def entrar(request):
    return render(request, "usuarios/entrar.html")


@never_cache
def acesso_interno(request):
    return render(request, "usuarios/acesso_interno.html")


def tem_permissao_modulo(user, modulo: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    role = getattr(getattr(user, "perfil_acesso", None), "role", PerfilAcesso.VISITANTE)
    perfil_normalizado = _normalizar_role(role)
    permissoes = {
        "reservas": {
            PerfilAcesso.RECEPCAO,
            PerfilAcesso.ADMIN_CONDOMINIO,
            PerfilAcesso.ADMIN_SISTEMA,
            PerfilAcesso.ADMIN,
        },
        "servicos": {
            PerfilAcesso.STAFF_LIMPEZA,
            PerfilAcesso.STAFF_LAVANDARIA,
            PerfilAcesso.STAFF_MANUTENCAO,
            PerfilAcesso.RECEPCAO,
            PerfilAcesso.ADMIN_CONDOMINIO,
            PerfilAcesso.ADMIN_SISTEMA,
            PerfilAcesso.ADMIN,
        },
        "restaurante": {
            PerfilAcesso.STAFF_RESTAURANTE,
            PerfilAcesso.RECEPCAO,
            PerfilAcesso.ADMIN_CONDOMINIO,
            PerfilAcesso.ADMIN_SISTEMA,
            PerfilAcesso.ADMIN,
        },
    }
    return perfil_normalizado in permissoes.get(modulo, set())


@never_cache
@login_required
def dashboard_reservas(request):
    if not tem_permissao_modulo(request.user, "reservas"):
        messages.warning(request, "Sem permissão para o módulo de Reservas.")
        return redirect("usuarios:acesso_interno")
    ctx = {
        "reservas_pendentes": Reserva.objects.filter(
            status__in=["pendente", "pre_reserva", "aguardando_pagamento", "pagamento_em_validacao", "aguardando_confirmacao"]
        ).count(),
        "reservas_confirmadas": Reserva.objects.filter(status="confirmada").count(),
    }
    # Simple timezone-safe stats
    from django.utils import timezone
    hoje_data = timezone.localdate()
    ctx["checkins_hoje"] = Reserva.objects.filter(data_inicio=hoje_data).count()
    ctx["checkouts_hoje"] = Reserva.objects.filter(data_fim=hoje_data).count()
    ctx["pagamentos_pendentes"] = Pagamento.objects.filter(status="pendente").count()
    return render(request, "interno/reservas/dashboard.html", ctx)


@never_cache
@login_required
def dashboard_servicos(request):
    if not tem_permissao_modulo(request.user, "servicos"):
        messages.warning(request, "Sem permissão para o módulo de Serviços.")
        return redirect("usuarios:acesso_interno")
    ctx = {
        "limpeza_total": PedidoLimpeza.objects.count(),
        "lavandaria_total": PedidoLavandaria.objects.count(),
        "pendentes": PedidoLimpeza.objects.filter(status="pendente").count()
        + PedidoLavandaria.objects.filter(status="pendente").count(),
        "em_execucao": PedidoLimpeza.objects.filter(status="em_curso").count()
        + PedidoLavandaria.objects.filter(status="em_curso").count(),
        "concluidos": PedidoLimpeza.objects.filter(status="concluido").count()
        + PedidoLavandaria.objects.filter(status="concluido").count(),
    }
    return render(request, "interno/servicos/dashboard.html", ctx)


@never_cache
@login_required
def dashboard_restaurante(request):
    if not tem_permissao_modulo(request.user, "restaurante"):
        messages.warning(request, "Sem permissão para o módulo de Restaurante.")
        return redirect("usuarios:acesso_interno")
    ctx = {
        "pedidos_quarto": PedidoRestaurante.objects.filter(origem="quarto").count(),
        "pedidos_presenciais": PedidoRestaurante.objects.filter(origem="presencial").count(),
        "pedidos_qr": PedidoRestaurante.objects.filter(origem="mesa_qr").count(),
        "em_preparacao": PedidoRestaurante.objects.filter(status="em_preparacao").count(),
        "prontos": PedidoRestaurante.objects.filter(status="pronto").count(),
        "entregues": PedidoRestaurante.objects.filter(status="entregue").count(),
        "menu_total": ProdutoRestaurante.objects.filter(disponivel=True).count(),
    }
    return render(request, "interno/restaurante/dashboard.html", ctx)


@never_cache
def acesso_interno_reservas(request):
    return redirect("usuarios:dashboard_reservas")


@never_cache
def acesso_interno_servicos(request):
    return redirect("usuarios:dashboard_servicos")


@never_cache
def acesso_interno_restaurante(request):
    return redirect("usuarios:dashboard_restaurante")
