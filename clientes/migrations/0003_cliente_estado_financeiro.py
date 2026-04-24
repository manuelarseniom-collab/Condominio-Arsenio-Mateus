from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0002_cliente_dados_profissionais"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="estado",
            field=models.CharField(
                choices=[("interessado", "Interessado"), ("ativo", "Ativo"), ("inativo", "Inativo")],
                default="interessado",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="cliente",
            name="situacao_financeira",
            field=models.CharField(
                choices=[("por_pagar", "Por pagar"), ("em_validacao", "Em validacao"), ("paga", "Paga")],
                default="por_pagar",
                max_length=20,
            ),
        ),
    ]
