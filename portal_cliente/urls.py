from django.urls import path

from . import views


app_name = "portal_cliente"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.home, name="cliente_dashboard"),
    path("reservas/", views.minhas_reservas, name="reservas"),
    path("reservas/lista/", views.minhas_reservas, name="cliente_reservas"),
    path("faturas/", views.minhas_faturas, name="faturas"),
    path("servicos/", views.servicos, name="servicos"),
    path("servicos/lista/", views.servicos, name="cliente_servicos"),
    path("servicos/limpeza/", views.servico_limpeza, name="servico_limpeza"),
    path("servicos/limpeza/solicitar/", views.servico_limpeza, name="cliente_solicitar_limpeza"),
    path("servicos/lavandaria/", views.servico_lavandaria, name="servico_lavandaria"),
    path("servicos/lavandaria/solicitar/", views.servico_lavandaria, name="cliente_solicitar_lavandaria"),
    path("servicos/restaurante/", views.servico_restaurante, name="servico_restaurante"),
    path("servicos/restaurante/solicitar/", views.servico_restaurante, name="cliente_solicitar_restaurante"),
    path("sem-acesso/", views.sem_acesso, name="sem_acesso"),
]
