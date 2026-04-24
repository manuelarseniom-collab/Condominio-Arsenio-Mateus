from django.urls import path

from . import views


app_name = "reservas"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("minhas/", views.minhas_reservas, name="minhas_reservas"),
    path("<int:reserva_id>/", views.detalhe_reserva, name="detalhe_reserva"),
    path("<int:reserva_id>/pagamento/", views.resumo_pagamento, name="resumo_pagamento"),
    path("<int:reserva_id>/editar/", views.editar_reserva, name="editar_reserva"),
]
