from django.urls import path

from . import views


app_name = "portal_cliente"

urlpatterns = [
    path("", views.home, name="home"),
    path("reservas/", views.minhas_reservas, name="reservas"),
    path("faturas/", views.minhas_faturas, name="faturas"),
    path("servicos/", views.servicos, name="servicos"),
    path("servicos/limpeza/", views.servico_limpeza, name="servico_limpeza"),
    path("servicos/lavandaria/", views.servico_lavandaria, name="servico_lavandaria"),
    path("servicos/restaurante/", views.servico_restaurante, name="servico_restaurante"),
    path("sem-acesso/", views.sem_acesso, name="sem_acesso"),
]
