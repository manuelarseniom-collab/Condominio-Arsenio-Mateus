from django.urls import path

from . import views


app_name = "faturacao"

urlpatterns = [
    path("", views.lista, name="lista"),
]
