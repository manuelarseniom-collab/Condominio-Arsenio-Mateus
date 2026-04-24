from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="perfilusuario",
            name="role",
            field=models.CharField(
                choices=[
                    ("visitante", "Visitante"),
                    ("cliente_pendente", "Cliente pendente"),
                    ("cliente_confirmado", "Cliente confirmado"),
                    ("staff_limpeza", "Staff limpeza"),
                    ("staff_lavandaria", "Staff lavandaria"),
                    ("staff_restaurante", "Staff restaurante"),
                    ("staff_manutencao", "Staff manutencao"),
                    ("recepcao", "Recepcao"),
                    ("admin", "Admin"),
                    ("admin_condominio", "Admin condominio"),
                    ("admin_sistema", "Admin sistema"),
                ],
                default="visitante",
                max_length=40,
            ),
        ),
    ]
