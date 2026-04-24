from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class PreReservaDadosForm(forms.Form):
    nome = forms.CharField(
        label="Nome completo",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "pre-input", "autocomplete": "name"}),
    )
    telefone = forms.CharField(
        label="Telefone",
        max_length=40,
        widget=forms.TextInput(attrs={"class": "pre-input", "autocomplete": "tel"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "pre-input", "autocomplete": "email"}),
    )
    data_inicio = forms.DateField(
        label="Check-in",
        widget=forms.DateInput(attrs={"type": "date", "class": "pre-input-date"}),
    )
    data_fim = forms.DateField(
        label="Check-out",
        widget=forms.DateInput(attrs={"type": "date", "class": "pre-input-date"}),
    )

    def clean(self):
        cleaned = super().clean()
        di = cleaned.get("data_inicio")
        df = cleaned.get("data_fim")
        if di and df and df <= di:
            raise ValidationError("A data de check-out deve ser posterior ao check-in.")
        return cleaned


class PreReservaContaForm(forms.Form):
    password1 = forms.CharField(
        label="Palavra-passe",
        widget=forms.PasswordInput(
            render_value=False,
            attrs={"class": "pre-input", "autocomplete": "new-password"},
        ),
        min_length=8,
    )
    password2 = forms.CharField(
        label="Confirmação da palavra-passe",
        widget=forms.PasswordInput(
            render_value=False,
            attrs={"class": "pre-input", "autocomplete": "new-password"},
        ),
    )

    def __init__(self, *args, email=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.email = email

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("As palavras-passe não coincidem.")
        return p2

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        if p1:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            dummy = User(username=self.email or "x", email=self.email or "")
            validate_password(p1, user=dummy)
        return cleaned
