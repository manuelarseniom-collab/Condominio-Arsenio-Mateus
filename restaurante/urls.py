from django.urls import path

from . import views


app_name = "restaurante"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("cozinha/", views.cozinha, name="cozinha"),
    path("relatorios/", views.relatorios, name="relatorios"),
    path("menu/mesa/<str:codigo_qr>/", views.menu_qr, name="menu_qr"),
    path("cozinha/ticket/<int:pedido_id>/", views.ticket_cozinha, name="ticket_cozinha"),
]
