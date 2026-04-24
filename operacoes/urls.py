from django.urls import path

from . import views

app_name = "operacoes"

urlpatterns = [
    path("staff/", views.painel_staff, name="painel_staff"),
    path("admin/", views.painel_admin_operacional, name="painel_admin"),
    path("cliente/historico-solicitacoes/", views.historico_solicitacoes_cliente, name="historico_cliente"),
]
