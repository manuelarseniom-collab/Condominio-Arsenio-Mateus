from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reservas", "0006_reserva_pedido_especial"),
    ]

    operations = [
        migrations.AddField(
            model_name="reserva",
            name="pagamento_confirmado_whatsapp",
            field=models.BooleanField(default=False, help_text="Pagamento confirmado por WhatsApp."),
        ),
    ]
