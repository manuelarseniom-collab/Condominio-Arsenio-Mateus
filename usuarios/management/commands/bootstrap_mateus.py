"""
Cria ou actualiza o utilizador operador pedido (Mateus / 2005).

Apenas para ambiente local / demonstração: a password é fraca e não passaria
nos validadores padrão do Django; não use em produção exposto à Internet.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Cria ou actualiza o utilizador Mateus com password 2005 (staff + superuser)."

    def handle(self, *args, **options):
        User = get_user_model()
        username = "Mateus"

        with transaction.atomic():
            user, created = User._default_manager.get_or_create(
                **{User.USERNAME_FIELD: username},
                defaults={
                    "email": "",
                    "is_staff": True,
                    "is_superuser": True,
                    "is_active": True,
                },
            )
            if not created:
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.save(update_fields=["is_staff", "is_superuser", "is_active"])

            user.set_password("2005")
            user.save(update_fields=["password"])

        acao = "criado" if created else "actualizado"
        self.stdout.write(
            self.style.SUCCESS(
                f"Utilizador {username!r} {acao}. Pode entrar no site /admin com essas credenciais."
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "Atenção: password fraca — use apenas em desenvolvimento ou rede fechada."
            )
        )
