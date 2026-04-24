from decimal import Decimal

from django import forms

from clientes.models import Cliente
from reservas.models import Reserva

from .models import Fatura


class FaturaForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(user__isnull=False).select_related("user").order_by("nome"),
        required=True,
        label="Cliente",
    )
    reserva = forms.ModelChoiceField(
        queryset=Reserva.objects.select_related("cliente", "unidade").order_by("-id"),
        required=False,
        label="Reserva",
    )
    incluir_reserva = forms.BooleanField(
        required=False,
        initial=True,
        label="Incluir item automático da reserva",
    )


class ItemManualForm(forms.Form):
    descricao = forms.CharField(max_length=255, required=False)
    quantidade = forms.IntegerField(min_value=1, required=False)
    preco_unitario = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"), required=False)

    def clean(self):
        cleaned = super().clean()
        descricao = (cleaned.get("descricao") or "").strip()
        quantidade = cleaned.get("quantidade")
        preco = cleaned.get("preco_unitario")
        if not descricao and not quantidade and not preco:
            return cleaned
        if not descricao:
            self.add_error("descricao", "Descrição obrigatória para item manual.")
        if not quantidade:
            self.add_error("quantidade", "Quantidade obrigatória.")
        if not preco:
            self.add_error("preco_unitario", "Preço unitário obrigatório.")
        return cleaned


class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Fatura
        fields = ["metodo_pagamento"]
        widgets = {
            "metodo_pagamento": forms.Select(
                choices=[
                    ("referencia_bancaria", "Online (referência bancária)"),
                    ("presencial_recepcao", "Presencial (recepção)"),
                ]
            )
        }
