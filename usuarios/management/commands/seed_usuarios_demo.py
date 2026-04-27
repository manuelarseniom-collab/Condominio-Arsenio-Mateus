from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from usuarios.models import PerfilUsuario

SENHA_COMUM_DEMO = "123456"
USUARIOS_DEMO = [
    ("trabalhador.demo", "trabalhador.demo@arsenio.local", "trabalhador", True, False),
    ("recepcao.demo", "recepcao.demo@arsenio.local", "recepcionista", True, False),
    ("restaurante.demo", "restaurante.demo@arsenio.local", "restaurante", True, False),
    ("servicos.demo", "servicos.demo@arsenio.local", "servicos", True, False),
    ("cliente.demo@arsenio.local", "cliente.demo@arsenio.local", "cliente_confirmado", False, False),
    ("admin.condominio", "admin.condominio@arsenio.local", "admin_condominio", True, False),
    ("admin.sistema", "admin.sistema@arsenio.local", "admin_sistema", True, True),
]


class Command(BaseCommand):
    help = "Repoe utilizadores demo e passwords padrao do portal Arsenio Mateus."

    def handle(self, *args, **options):
        user_model = get_user_model()

        with transaction.atomic():
            for username, email, perfil, is_staff, is_superuser in USUARIOS_DEMO:
                user, created = user_model._default_manager.update_or_create(
                    **{user_model.USERNAME_FIELD: username},
                    defaults={
                        "email": email,
                        "is_active": True,
                        "is_staff": is_staff,
                        "is_superuser": is_superuser,
                    },
                )

                user.set_password(SENHA_COMUM_DEMO)
                user.save(update_fields=["password"])

                perfil_obj, _ = PerfilUsuario.objects.get_or_create(user=user)
                perfil_obj.role = perfil
                perfil_obj.ativo = True
                perfil_obj.save(update_fields=["role", "ativo", "atualizado_em"])

                estado = "criado" if created else "atualizado"
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{username} {estado} | perfil={perfil} | password={SENHA_COMUM_DEMO}"
                    )
                )

        self.stdout.write(self.style.SUCCESS("Utilizadores demo repostos com sucesso."))
