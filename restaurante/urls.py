from django.urls import path

from . import views


app_name = "restaurante"

urlpatterns = [
    path("", views.lista, name="lista"),
]
