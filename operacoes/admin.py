from django.contrib import admin

from .models import AtribuicaoStaff, Servico, SolicitacaoServico

admin.site.register(Servico)
admin.site.register(SolicitacaoServico)
admin.site.register(AtribuicaoStaff)
