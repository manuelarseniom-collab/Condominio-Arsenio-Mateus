from django import forms

from .models import Depoimento


class DepoimentoForm(forms.ModelForm):
    class Meta:
        model = Depoimento
        fields = ["titulo", "comentario", "avaliacao"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "comentario": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "avaliacao": forms.Select(
                choices=[
                    (1, "1 estrela"),
                    (2, "2 estrelas"),
                    (3, "3 estrelas"),
                    (4, "4 estrelas"),
                    (5, "5 estrelas"),
                ],
                attrs={"class": "form-select"},
            ),
        }

    def clean_comentario(self):
        comentario = (self.cleaned_data.get("comentario") or "").strip()
        if not comentario:
            raise forms.ValidationError("O comentário não pode estar vazio.")
        return comentario
