# Generated manually for disponibilidade por quartos

from django.db import migrations, models


def popular_quartos(apps, schema_editor):
    Unidade = apps.get_model("unidades", "Unidade")
    for u in Unidade.objects.all():
        t = (u.tipo or "").strip().upper()
        if t == "T0":
            u.numero_quartos = 0
        elif t == "T1":
            u.numero_quartos = 1
        elif t == "T2":
            u.numero_quartos = 2
        elif t == "T3":
            u.numero_quartos = 3
        elif "PENT" in t or "MASTER" in t:
            u.numero_quartos = 4
        else:
            u.numero_quartos = None
        u.save(update_fields=["numero_quartos"])


class Migration(migrations.Migration):

    dependencies = [
        ("unidades", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="unidade",
            name="numero_quartos",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Número de quartos; se vazio, infere-se pela tipologia (T0..T3, penthouse).",
                null=True,
            ),
        ),
        migrations.RunPython(popular_quartos, migrations.RunPython.noop),
    ]
