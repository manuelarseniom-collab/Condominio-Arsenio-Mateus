from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservas", "0004_reserva_finalidade_estadia"),
    ]

    operations = [
        migrations.AddField(
            model_name="reserva",
            name="cidade",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="reserva",
            name="contacto_alternativo",
            field=models.CharField(blank=True, default="", max_length=40),
        ),
        migrations.AddField(
            model_name="reserva",
            name="data_nascimento",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="reserva",
            name="email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
        migrations.AddField(
            model_name="reserva",
            name="morada",
            field=models.CharField(blank=True, default="", max_length=180),
        ),
        migrations.AddField(
            model_name="reserva",
            name="nacionalidade",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="reserva",
            name="nome_completo",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="reserva",
            name="numero_documento_identificacao",
            field=models.CharField(blank=True, default="", max_length=60),
        ),
        migrations.AddField(
            model_name="reserva",
            name="pais_residencia",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="reserva",
            name="preferencia_contacto",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="reserva",
            name="telefone",
            field=models.CharField(blank=True, default="", max_length=40),
        ),
        migrations.AddField(
            model_name="reserva",
            name="tipo_documento",
            field=models.CharField(blank=True, default="", max_length=40),
        ),
    ]
