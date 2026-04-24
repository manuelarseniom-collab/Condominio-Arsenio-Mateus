from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservas", "0005_reserva_snapshot_dados_cliente"),
    ]

    operations = [
        migrations.AddField(
            model_name="reserva",
            name="pedido_especial",
            field=models.TextField(blank=True, default=""),
        ),
    ]
