from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from .views import (
    LoginAdminView,
    LoginClienteView,
    LoginStaffView,
    UsuarioLoginView,
    UsuarioLogoutView,
    acesso_interno,
    dashboard_reservas,
    dashboard_restaurante,
    dashboard_servicos,
    cozinha_restaurante,
    menu_restaurante_admin,
    novo_pedido_restaurante,
    pedidos_restaurante,
    acesso_interno_reservas,
    acesso_interno_restaurante,
    acesso_interno_servicos,
    entrar,
)


app_name = "usuarios"

_password_reset_kwargs = {
    "template_name": "registration/password_reset_form.html",
    "email_template_name": "registration/password_reset_email.txt",
    "subject_template_name": "registration/password_reset_subject.txt",
    "success_url": reverse_lazy("usuarios:password_reset_done"),
}

urlpatterns = [
    path("entrar/", entrar, name="entrar"),
    path("acesso-interno/", acesso_interno, name="acesso_interno"),
    path("interno/reservas/", dashboard_reservas, name="dashboard_reservas"),
    path("interno/servicos/", dashboard_servicos, name="dashboard_servicos"),
    path("interno/restaurante/", dashboard_restaurante, name="dashboard_restaurante"),
    path("interno/restaurante/pedido/novo/", novo_pedido_restaurante, name="novo_pedido_restaurante"),
    path("interno/restaurante/pedidos/", pedidos_restaurante, name="pedidos_restaurante"),
    path("interno/restaurante/cozinha/", cozinha_restaurante, name="cozinha_restaurante"),
    path("interno/restaurante/menu/", menu_restaurante_admin, name="menu_restaurante_admin"),
    path("acesso-interno/reservas/", acesso_interno_reservas, name="acesso_interno_reservas"),
    path("acesso-interno/servicos/", acesso_interno_servicos, name="acesso_interno_servicos"),
    path("acesso-interno/restaurante/", acesso_interno_restaurante, name="acesso_interno_restaurante"),
    path("login/", UsuarioLoginView.as_view(), name="login"),
    path("login/interno/", LoginStaffView.as_view(), name="login_interno"),
    path("login/cliente/", LoginClienteView.as_view(), name="login_cliente"),
    path("login/staff/", LoginStaffView.as_view(), name="login_staff"),
    path("login/admin/", LoginAdminView.as_view(), name="login_admin"),
    path("password-reset/", auth_views.PasswordResetView.as_view(**_password_reset_kwargs), name="password_reset"),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "password-reset/confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("usuarios:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path("logout/", UsuarioLogoutView.as_view(), name="logout"),
]
