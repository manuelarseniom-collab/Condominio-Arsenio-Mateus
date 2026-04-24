from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from reservas.public_views import buscar_apartamentos, iniciar_pre_reserva

handler403 = "condominio_web.views.erro_403"


urlpatterns = [
    path("admin/", admin.site.urls),
    path("apartamentos/disponiveis/", buscar_apartamentos, name="buscar_apartamentos"),
    path("reservas/pre-reserva/<int:apartment_id>/", iniciar_pre_reserva, name="iniciar_pre_reserva"),
    path("", include("site_publico.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("clientes/", include("clientes.urls")),
    path("unidades/", include("unidades.urls")),
    path("reservas/", include("reservas.urls")),
    path("limpeza/", include("limpeza.urls")),
    path("lavandaria/", include("lavandaria.urls")),
    path("restaurante/", include("restaurante.urls")),
    path("faturacao/", include("faturacao.urls")),
    path("relatorios/", include("relatorios.urls")),
    path("conta/", include("portal_cliente.urls")),
    path("painel-cliente/", RedirectView.as_view(pattern_name="portal_cliente:home", permanent=False)),
    path("painel-interno/", RedirectView.as_view(pattern_name="dashboard:home", permanent=False)),
    path("operacoes/", include("operacoes.urls")),
    path("", include("usuarios.urls")),
]
