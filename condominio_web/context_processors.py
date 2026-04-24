from django.conf import settings

from usuarios.models import PerfilAcesso
from usuarios.perfil import get_perfil_atual, get_perfil_atual_label
from usuarios.roles import (
    ROLES_ADMIN,
    ROLES_CLIENTE,
    ROLES_INTERNOS,
    ROLES_RECECAO,
    ROLES_STAFF,
    get_user_role,
    role_display_name,
)


def navigation_context(request):
    role = get_user_role(getattr(request, "user", None))
    profile = get_perfil_atual(request)
    contact_phone = getattr(settings, "CONTACT_PHONE", "")
    contact_phone_href = "".join(ch for ch in contact_phone if ch.isdigit() or ch == "+")
    return {
        "current_role": role,
        "current_role_label": role_display_name(role),
        "current_profile": profile,
        "current_profile_label": get_perfil_atual_label(request),
        "perfil_atual": profile,
        "perfil_atual_label": get_perfil_atual_label(request),
        "is_visitante": profile == "visitante_interessado",
        "is_cliente": profile == "cliente",
        "is_rececao": role in ROLES_RECECAO,
        "is_staff": profile == "trabalhador" and role in ROLES_STAFF,
        "is_admin": profile == "administrador",
        "is_interno": profile in {"trabalhador", "administrador"},
        "contact_email": getattr(settings, "CONTACT_EMAIL", ""),
        "contact_phone": contact_phone,
        "contact_phone_href": contact_phone_href,
    }
