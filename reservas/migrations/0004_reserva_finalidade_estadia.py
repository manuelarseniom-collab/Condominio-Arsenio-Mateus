from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservas", "0003_reserva_pagamento_hospedes_estados"),
    ]

    operations = [
        migrations.AddField(
            model_name="reserva",
            name="finalidade_estadia",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
    ]
