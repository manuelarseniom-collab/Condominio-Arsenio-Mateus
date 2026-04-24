from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("unidades", "0003_repair_numero_quartos_sqlite"),
    ]

    operations = [
        migrations.AddField(
            model_name="unidade",
            name="capacidade",
            field=models.PositiveSmallIntegerField(default=2),
        ),
        migrations.AddField(
            model_name="unidade",
            name="descricao",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="unidade",
            name="observacoes",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="unidade",
            name="possui_sofa_cama",
            field=models.BooleanField(default=False),
        ),
    ]
