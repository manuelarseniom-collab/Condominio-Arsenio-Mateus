from django.urls import path

from . import views


app_name = "faturacao"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("emitir/", views.emitir_fatura, name="emitir"),
    path("<int:fatura_id>/", views.detalhe, name="detalhe"),
    path("<int:fatura_id>/imprimir/", views.imprimir, name="imprimir"),
    path("<int:fatura_id>/whatsapp/", views.whatsapp, name="whatsapp"),
]
