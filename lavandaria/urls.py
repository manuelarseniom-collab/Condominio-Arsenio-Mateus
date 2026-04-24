from django.urls import path

from . import views


app_name = "lavandaria"

urlpatterns = [
    path("", views.lista, name="lista"),
]
