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
        return self.get_response(request)
