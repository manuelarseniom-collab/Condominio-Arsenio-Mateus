from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm


class SecureAuthenticationForm(AuthenticationForm):
    username = forms.CharField(required=False, widget=forms.HiddenInput())
    password = forms.CharField(required=False, widget=forms.HiddenInput())
    login_usuario = forms.CharField(
        label="Utilizador",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "new-password",
                "autocapitalize": "off",
                "spellcheck": "false",
            }
        ),
    )
    login_senha = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean(self):
        username = self.cleaned_data.get("login_usuario")
        password = self.cleaned_data.get("login_senha")

        if username is not None and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
