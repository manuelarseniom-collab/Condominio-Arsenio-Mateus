from django.shortcuts import redirect
from django.urls import reverse

from usuarios.models import PerfilAcesso


class ClienteConfirmadoMiddleware:
    """
    Garante que a area reservada de cliente seja acessada apenas por
    cliente com reserva confirmada/ativa.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/conta/") and request.user.is_authenticated:
            if hasattr(request.user, "perfil_acesso"):
                role = request.user.perfil_acesso.role
                if role not in (
                    PerfilAcesso.CLIENTE_CONFIRMADO,
                    PerfilAcesso.ADMIN,
                    PerfilAcesso.ADMIN_CONDOMINIO,
                    PerfilAcesso.ADMIN_SISTEMA,
                    PerfilAcesso.RECEPCAO,
                ):
                    return redirect(reverse("portal_cliente:sem_acesso"))
        response = self.get_response(request)

        # Evita cache de páginas sensíveis (login e áreas autenticadas).
        if (
            request.path.startswith("/login/")
            or request.path.startswith("/entrar/")
            or request.path.startswith("/acesso-interno/")
            or (
                request.user.is_authenticated
                and (
                    request.path.startswith("/conta/")
                    or request.path.startswith("/dashboard/")
                    or request.path.startswith("/reservas/")
                    or request.path.startswith("/faturacao/")
                    or request.path.startswith("/operacoes/")
                )
            )
        ):
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
        return response
