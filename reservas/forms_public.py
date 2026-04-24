import re

from django import forms
from django.core.exceptions import ValidationError


class BuscaDisponibilidadeForm(forms.Form):
    TIPOLOGIA_CHOICES = (
        ("", "Qualquer tipologia"),
        ("T0", "T0"),
        ("T1", "T1"),
        ("T2", "T2"),
        ("T3", "T3"),
        ("PENTHOUSE", "Penthouse"),
    )

    data_checkin = forms.DateField(
        label="Data de entrada",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    data_checkout = forms.DateField(
        label="Data de saída",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    tipologia = forms.ChoiceField(
        label="Tipologia",
        choices=TIPOLOGIA_CHOICES,
        required=False,
    )
    andar = forms.CharField(
        label="Andar",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Opcional", "min": "0", "max": "50"}),
    )

    def clean(self):
        cleaned = super().clean()
        di = cleaned.get("data_checkin")
        df = cleaned.get("data_checkout")
        if di and df and df <= di:
            raise ValidationError("A data de saída deve ser posterior à data de entrada.")

        raw_andar = (cleaned.get("andar") or "").strip()
        if raw_andar == "":
            cleaned["andar"] = None
        else:
            try:
                andar = int(raw_andar)
            except ValueError:
                self.add_error("andar", "Indique um número válido.")
            else:
                if 0 <= andar <= 50:
                    cleaned["andar"] = andar
                else:
                    self.add_error("andar", "O valor deve estar entre 0 e 50.")
        return cleaned


class IniciarPreReservaForm(forms.Form):
    nome_cliente = forms.CharField(
        label="Nome completo",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "name"}),
    )
    telefone = forms.CharField(
        label="Telefone",
        max_length=40,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "tel"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )
    nacionalidade = forms.CharField(
        label="Nacionalidade",
        max_length=80,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    tipo_documento = forms.ChoiceField(
        label="Tipo de documento",
        choices=(
            ("", "Selecione"),
            ("BI", "Bilhete de Identidade"),
            ("PASSAPORTE", "Passaporte"),
            ("TITULO_RESIDENCIA", "Titulo de Residencia"),
            ("OUTRO", "Outro"),
        ),
    )
    numero_documento_identificacao = forms.CharField(
        label="N.º do documento de identificação",
        max_length=60,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    data_nascimento = forms.DateField(
        label="Data de nascimento",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    data_checkin = forms.DateField(
        label="Data de entrada",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    data_checkout = forms.DateField(
        label="Data de saída",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    numero_hospedes = forms.IntegerField(
        label="Número de hóspedes",
        min_value=1,
        max_value=30,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    observacoes = forms.CharField(
        label="Observações",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
    finalidade_estadia = forms.CharField(
        label="Finalidade da estadia",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Lazer, trabalho, família, etc."}),
    )
    morada = forms.CharField(
        label="Morada",
        required=False,
        max_length=180,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    cidade = forms.CharField(
        label="Cidade",
        required=False,
        max_length=80,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    pais_residencia = forms.CharField(
        label="País de residência",
        required=False,
        max_length=80,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    empresa_instituicao = forms.CharField(
        label="Empresa ou instituição",
        required=False,
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    pedido_especial = forms.CharField(
        label="Pedido especial",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )
    contacto_alternativo = forms.CharField(
        label="Contacto alternativo",
        required=False,
        max_length=40,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    preferencia_contacto = forms.ChoiceField(
        label="Preferência de contacto",
        required=False,
        choices=(("", "Sem preferência"), ("email", "Email"), ("telefone", "Telefone"), ("whatsapp", "WhatsApp")),
    )
    def clean(self):
        cleaned = super().clean()
        di = cleaned.get("data_checkin")
        df = cleaned.get("data_checkout")
        if di and df and df <= di:
            raise ValidationError("A data de saída deve ser posterior à data de entrada.")
        telefone = (cleaned.get("telefone") or "").strip()
        if telefone and not re.fullmatch(r"[+\d][\d\s\-()]{6,30}", telefone):
            self.add_error("telefone", "Indique um número de telefone válido.")
        return cleaned


class EditarReservaForm(forms.Form):
    nome_completo = forms.CharField(label="Nome completo", max_length=120)
    telefone = forms.CharField(label="Telefone", max_length=40)
    email = forms.EmailField(label="Email")
    nacionalidade = forms.CharField(label="Nacionalidade", max_length=80)
    tipo_documento = forms.CharField(label="Tipo de documento", max_length=40)
    numero_documento_identificacao = forms.CharField(label="N.º do documento", max_length=60)
    data_nascimento = forms.DateField(label="Data de nascimento", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    morada = forms.CharField(label="Morada", max_length=180, required=False)
    cidade = forms.CharField(label="Cidade", max_length=80, required=False)
    pais_residencia = forms.CharField(label="País de residência", max_length=80, required=False)
    contacto_alternativo = forms.CharField(label="Contacto alternativo", max_length=40, required=False)
    preferencia_contacto = forms.CharField(label="Preferência de contacto", max_length=20, required=False)
    data_checkin = forms.DateField(label="Data de entrada", widget=forms.DateInput(attrs={"type": "date"}))
    data_checkout = forms.DateField(label="Data de saída", widget=forms.DateInput(attrs={"type": "date"}))
    numero_hospedes = forms.IntegerField(label="Número de hóspedes", min_value=1, max_value=30)
    finalidade_estadia = forms.CharField(label="Finalidade da estadia", max_length=120, required=False)
    observacoes = forms.CharField(label="Observações", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    pedido_especial = forms.CharField(label="Pedido especial", required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def clean(self):
        cleaned = super().clean()
        di = cleaned.get("data_checkin")
        df = cleaned.get("data_checkout")
        if di and df and df <= di:
            raise ValidationError("A data de saída deve ser posterior à data de entrada.")
        telefone = (cleaned.get("telefone") or "").strip()
        if telefone and not re.fullmatch(r"[+\d][\d\s\-()]{6,30}", telefone):
            self.add_error("telefone", "Indique um número de telefone válido.")
        return cleaned
