from django.urls import path

from . import views


app_name = "limpeza"

urlpatterns = [
    path("", views.lista, name="lista"),
]
