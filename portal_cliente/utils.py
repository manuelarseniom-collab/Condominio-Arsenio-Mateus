from django.utils import timezone

from clientes.models import Cliente


def obter_cliente(request):
    if not request.user.is_authenticated:
        return None
    return Cliente.objects.filter(user=request.user).first()


def contexto_servicos_portal(request):
    """
    Serviços no portal só a partir do 1.º dia da estadia (reserva confirmada ou ativa).
    Devolve flags e mensagem para templates.
    """
    hoje = timezone.localdate()
    cliente = obter_cliente(request)
    if not cliente:
        return {
            "pode_solicitar_servicos": False,
            "mensagem_servicos": (
                "Este serviço só fica disponível após reserva confirmada e check-in realizado."
            ),
        }

    reservas = cliente.reservas.filter(status__in=["ativa"]).order_by("data_inicio")
    for r in reservas:
        if r.data_inicio <= hoje <= r.data_fim:
            return {
                "pode_solicitar_servicos": True,
                "mensagem_servicos": None,
                "reserva_servicos": r,
            }

    return {
        "pode_solicitar_servicos": False,
        "mensagem_servicos": (
            "Para solicitar este serviço, é necessário ter uma reserva confirmada e ter iniciado a sua estadia com check-in."
        ),
    }