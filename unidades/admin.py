from django.contrib import admin

from .models import Unidade


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "andar", "tipo", "preco_mensal", "disponivel")
