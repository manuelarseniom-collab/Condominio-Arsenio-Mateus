from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

from usuarios.forms import SecureAuthenticationForm
from usuarios.models import PerfilAcesso


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
        response = super().form_valid(form)
        role = getattr(getattr(self.request.user, "perfil_acesso", None), "role", PerfilAcesso.VISITANTE)
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
            return response
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
