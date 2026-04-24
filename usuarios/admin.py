from django.contrib import admin

from usuarios.models import Notificacao, PerfilUsuario

admin.site.register(PerfilUsuario)
admin.site.register(Notificacao)
