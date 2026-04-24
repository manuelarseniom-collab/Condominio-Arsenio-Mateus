"""
Garante que a coluna numero_quartos existe na tabela quando o esquema está
desalinhado (ex.: SQLite sem migrate, ou django_migrations inconsistente).
"""

from django.db import migrations


def _coluna_existe(cursor, tabela: str, coluna: str, vendor: str) -> bool:
    if vendor == "sqlite":
        cursor.execute(f'PRAGMA table_info("{tabela}")')
        return any(row[1] == coluna for row in cursor.fetchall())
    if vendor == "mysql":
        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
              AND COLUMN_NAME = %s
            """,
            [tabela, coluna],
        )
        return cursor.fetchone()[0] > 0
    if vendor == "postgresql":
        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
            """,
            [tabela, coluna],
        )
        return cursor.fetchone()[0] > 0
    return True


def adicionar_coluna_se_faltar(apps, schema_editor):
    connection = schema_editor.connection
    vendor = connection.vendor
    tabela = "unidades_unidade"
    coluna = "numero_quartos"

    with connection.cursor() as cursor:
        if _coluna_existe(cursor, tabela, coluna, vendor):
            return
        if vendor == "sqlite":
            cursor.execute(
                f'ALTER TABLE "{tabela}" ADD COLUMN "{coluna}" integer NULL'
            )
        elif vendor == "mysql":
            cursor.execute(
                f"ALTER TABLE `{tabela}` ADD COLUMN `{coluna}` SMALLINT UNSIGNED NULL"
            )
        elif vendor == "postgresql":
            cursor.execute(
                f'ALTER TABLE "{tabela}" ADD COLUMN "{coluna}" smallint NULL'
            )


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
        ("unidades", "0002_unidade_numero_quartos"),
    ]

    operations = [
        migrations.RunPython(adicionar_coluna_se_faltar, migrations.RunPython.noop),
        migrations.RunPython(popular_quartos, migrations.RunPython.noop),
    ]
