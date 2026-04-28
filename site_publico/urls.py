from django.urls import path

from depoimentos import views as depoimentos_views
from . import views
from .pre_reserva_views import (
    pre_reserva_conta,
    pre_reserva_dados,
    pre_reserva_escolher_unidade,
    pre_reserva_sucesso,
)


app_name = "site_publico"

urlpatterns = [
    path("", views.home, name="home"),
    path("disponibilidade/", views.disponibilidade, name="disponibilidade"),
    path("como-funciona/", views.como_funciona, name="como_funciona"),
    path("pre-reserva/", pre_reserva_escolher_unidade, name="pre_reserva_escolher"),
    path("pre-reserva/dados/", pre_reserva_dados, name="pre_reserva_dados"),
    path("pre-reserva/conta/", pre_reserva_conta, name="pre_reserva_conta"),
    path("pre-reserva/concluido/", pre_reserva_sucesso, name="pre_reserva_sucesso"),
    path("apartamentos/", views.apartamentos, name="apartamentos"),
    path("servicos/", views.servicos, name="servicos"),
    path("servicos-publicos/", views.servicos_publicos, name="servicos_publicos"),
    path("servicos/solicitar/", views.solicitar_servico, name="solicitar_servico"),
    path("restaurante/", views.restaurante, name="restaurante"),
    path("restaurante-publico/", views.restaurante_publico, name="restaurante_publico"),
    path("contactos/", views.contactos, name="contactos"),
    path("faq/", views.faq, name="faq"),
    path("depoimentos/", depoimentos_views.depoimentos_publicos, name="depoimentos"),
    path("depoimentos/novo/", depoimentos_views.criar_depoimento, name="criar_depoimento"),
    path("painel-admin/depoimentos/", depoimentos_views.admin_depoimentos, name="admin_depoimentos"),
]
