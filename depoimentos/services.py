from reservas.models import Reserva
from usuarios.roles import PERFIL_CLIENTE, get_user_profile


def cliente_pode_deixar_depoimento(user) -> bool:
    return get_user_profile(user) == PERFIL_CLIENTE


def reserva_elegivel_para_depoimento(user):
    if not user or not user.is_authenticated:
        return None
    return (
        Reserva.objects.filter(
            cliente__user=user,
            status__in=["ativa", "concluida"],
        )
        .order_by("-data_inicio")
        .first()
    )
