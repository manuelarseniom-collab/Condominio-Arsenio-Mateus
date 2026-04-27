from usuarios.models import PerfilAcesso

ROLE_ALIASES = {
    "trabalhador": "trabalhador",
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
}


ROLES_CLIENTE = {
    PerfilAcesso.CLIENTE_PENDENTE,
    PerfilAcesso.CLIENTE_CONFIRMADO,
}

ROLES_RECECAO = {
    PerfilAcesso.RECEPCAO,
}

ROLES_STAFF = {
    PerfilAcesso.STAFF_LIMPEZA,
    PerfilAcesso.STAFF_LAVANDARIA,
    PerfilAcesso.STAFF_RESTAURANTE,
    PerfilAcesso.STAFF_MANUTENCAO,
    "trabalhador",
}

ROLES_ADMIN = {
    PerfilAcesso.ADMIN,
    PerfilAcesso.ADMIN_CONDOMINIO,
    PerfilAcesso.ADMIN_SISTEMA,
}

ROLES_INTERNOS = ROLES_RECECAO | ROLES_STAFF | ROLES_ADMIN

PERFIL_VISITANTE_INTERESSADO = "visitante_interessado"
PERFIL_CLIENTE = "cliente"
PERFIL_TRABALHADOR = "trabalhador"
PERFIL_ADMINISTRADOR = "administrador"


def get_user_role(user):
    if not user or not user.is_authenticated:
        return PerfilAcesso.VISITANTE
    role = None
    if hasattr(user, "perfil_acesso"):
        role = user.perfil_acesso.role
    role = role or getattr(user, "perfil", None) or getattr(user, "role", None) or PerfilAcesso.VISITANTE
    role = str(role).strip().lower()
    return ROLE_ALIASES.get(role, role)


def role_display_name(role: str) -> str:
    labels = {
        PerfilAcesso.VISITANTE: "Visitante interessado",
        PerfilAcesso.CLIENTE_PENDENTE: "Cliente com pré-reserva",
        PerfilAcesso.CLIENTE_CONFIRMADO: "Cliente confirmado",
        PerfilAcesso.STAFF_LIMPEZA: "Trabalhador (Limpeza)",
        PerfilAcesso.STAFF_LAVANDARIA: "Trabalhador (Lavandaria)",
        PerfilAcesso.STAFF_RESTAURANTE: "Trabalhador (Restaurante)",
        PerfilAcesso.STAFF_MANUTENCAO: "Trabalhador (Manutenção)",
        PerfilAcesso.RECEPCAO: "Recepcionista",
        PerfilAcesso.ADMIN: "Administrador",
        PerfilAcesso.ADMIN_CONDOMINIO: "Administrador do condomínio",
        PerfilAcesso.ADMIN_SISTEMA: "Administrador do sistema",
    }
    return labels.get(role, "Visitante interessado")


def get_user_profile(user) -> str:
    """Normaliza o perfil funcional que deve ser exibido no portal."""
    role = get_user_role(user)
    if not user or not user.is_authenticated:
        return PERFIL_VISITANTE_INTERESSADO
    if user.is_superuser or role in ROLES_ADMIN:
        return PERFIL_ADMINISTRADOR
    if role in ROLES_INTERNOS:
        return PERFIL_TRABALHADOR
    if role in ROLES_CLIENTE or hasattr(user, "perfil_cliente"):
        return PERFIL_CLIENTE
    return PERFIL_VISITANTE_INTERESSADO


def profile_display_name(profile: str) -> str:
    labels = {
        PERFIL_VISITANTE_INTERESSADO: "Visitante interessado",
        PERFIL_CLIENTE: "Cliente",
        PERFIL_TRABALHADOR: "Trabalhador",
        PERFIL_ADMINISTRADOR: "Administrador",
    }
    return labels.get(profile, "Visitante interessado")
