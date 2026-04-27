from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from usuarios.models import PerfilAcesso, PerfilUsuario


class Command(BaseCommand):
    help = "Cria utilizadores internos de teste para o portal Arsenio Mateus."

    def handle(self, *args, **options):
        user_model = get_user_model()

        usuarios = [
            {
                "username": "trabalhador.demo",
                "email": "trabalhador.demo@arsenio.local",
                "password": "123456",
                "perfil_seed": "trabalhador",
                "perfil_role": "trabalhador",
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "username": "recepcao.demo",
                "email": "recepcao.demo@arsenio.local",
                "password": "123456",
                "perfil_seed": "recepcionista",
                "perfil_role": PerfilAcesso.RECEPCAO,
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "username": "restaurante.demo",
                "email": "restaurante.demo@arsenio.local",
                "password": "123456",
                "perfil_seed": "restaurante",
                "perfil_role": PerfilAcesso.STAFF_RESTAURANTE,
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "username": "servicos.demo",
                "email": "servicos.demo@arsenio.local",
                "password": "123456",
                "perfil_seed": "servicos",
                "perfil_role": PerfilAcesso.STAFF_MANUTENCAO,
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "username": "admin.condominio",
                "email": "admin.condominio@arsenio.local",
                "password": "123456",
                "perfil_seed": "admin_condominio",
                "perfil_role": PerfilAcesso.ADMIN_CONDOMINIO,
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "username": "admin.sistema",
                "email": "admin.sistema@arsenio.local",
                "password": "123456",
                "perfil_seed": "admin_sistema",
                "perfil_role": PerfilAcesso.ADMIN_SISTEMA,
                "is_staff": True,
                "is_superuser": True,
            },
        ]

        for dados in usuarios:
            username = dados["username"]
            password = dados["password"]

            user, created = user_model._default_manager.get_or_create(
                **{user_model.USERNAME_FIELD: username},
                defaults={
                    "email": dados["email"],
                    "is_staff": dados["is_staff"],
                    "is_superuser": dados["is_superuser"],
                    "is_active": True,
                },
            )

            user.email = dados["email"]
            user.is_staff = dados["is_staff"]
            user.is_superuser = dados["is_superuser"]
            user.is_active = True
            user.set_password(password)
            user.save(update_fields=["email", "is_staff", "is_superuser", "is_active", "password"])

            perfil, _ = PerfilUsuario.objects.get_or_create(
                user=user,
                defaults={"role": dados["perfil_role"], "ativo": True},
            )
            perfil.role = dados["perfil_role"]
            perfil.ativo = True
            perfil.save(update_fields=["role", "ativo", "atualizado_em"])

            estado = "criado" if created else "atualizado"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{username} {estado} com perfil {dados['perfil_seed']} ({dados['perfil_role']})."
                )
            )

        self.stdout.write(self.style.SUCCESS("Utilizadores internos criados/atualizados com sucesso."))
