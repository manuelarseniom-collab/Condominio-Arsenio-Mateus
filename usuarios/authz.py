from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse

from usuarios.perfil import get_perfil_atual
from usuarios.roles import get_user_role


def _get_role(user):
    return get_user_role(user)


def role_required(*roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            role = _get_role(request.user)
            if role in roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            messages.error(request, "Acesso não autorizado para este perfil.")
            return redirect("usuarios:entrar")

        return wrapped

    return decorator


def _perfil_required(perfis_permitidos, redirect_name):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            perfil = get_perfil_atual(request)
            if perfil in perfis_permitidos:
                return view_func(request, *args, **kwargs)
            messages.error(request, "Acesso não autorizado para este perfil.")
            return redirect(redirect_name)

        return wrapped

    return decorator


def cliente_required(view_func):
    return _perfil_required({"cliente"}, "usuarios:login_cliente")(view_func)


def trabalhador_required(view_func):
    return _perfil_required({"trabalhador"}, "usuarios:login_staff")(view_func)


def administrador_required(view_func):
    return _perfil_required({"administrador"}, "usuarios:login_admin")(view_func)


def interno_required(view_func):
    return _perfil_required({"trabalhador", "administrador"}, "usuarios:acesso_interno")(view_func)


def modulo_required(modulo):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                login_url = f"{reverse('usuarios:login_interno')}?next={request.path}"
                return redirect(login_url)
            from usuarios.views import tem_permissao_modulo  # import local para evitar ciclo

            if not tem_permissao_modulo(request.user, modulo):
                messages.warning(request, f"Sem permissão para o módulo de {modulo.title()}.")
                return redirect("usuarios:acesso_interno")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
