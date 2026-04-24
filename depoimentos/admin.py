from django.contrib import admin

from .models import Depoimento


@admin.register(Depoimento)
class DepoimentoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "user", "avaliacao", "status", "publicado", "abusivo", "criado_em")
    list_filter = ("status", "publicado", "abusivo", "avaliacao", "criado_em")
    search_fields = ("titulo", "comentario", "user__username", "user__email")
    actions = ["aprovar", "rejeitar", "ocultar", "marcar_abusivo"]

    @admin.action(description="Aprovar depoimentos selecionados")
    def aprovar(self, request, queryset):
        queryset.update(status="aprovado", publicado=True, abusivo=False)

    @admin.action(description="Rejeitar depoimentos selecionados")
    def rejeitar(self, request, queryset):
        queryset.update(status="rejeitado", publicado=False)

    @admin.action(description="Ocultar depoimentos selecionados")
    def ocultar(self, request, queryset):
        queryset.update(status="oculto", publicado=False)

    @admin.action(description="Marcar como abusivo")
    def marcar_abusivo(self, request, queryset):
        queryset.update(
            abusivo=True,
            publicado=False,
            status="rejeitado",
            motivo_moderacao="Depoimento removido por violar as regras de publicação.",
        )
