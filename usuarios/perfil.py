from usuarios.roles import get_user_profile, profile_display_name


def get_perfil_atual(request) -> str:
    """Single source of truth do perfil ativo na sessão atual."""
    return get_user_profile(getattr(request, "user", None))


def get_perfil_atual_label(request) -> str:
    return profile_display_name(get_perfil_atual(request))
