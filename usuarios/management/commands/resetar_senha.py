import getpass
import sys

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from usuarios.user_audit import gerar_password_aleatoria


class Command(BaseCommand):
    help = (
        "Redefine a password de um utilizador de forma segura: não lê nem mostra hashes. "
        "Por omissão gera password aleatória (mostrada uma vez) ou use --senha / leitura interativa."
    )

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Nome de utilizador (USERNAME_FIELD).")
        parser.add_argument(
            "--senha",
            type=str,
            default=None,
            help="Definir password manualmente (atenção ao histórico da shell).",
        )
        parser.add_argument(
            "--interactive",
            action="store_true",
            help="Pedir a nova password sem eco (getpass), em vez de gerar aleatoriamente.",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            dest="skip_confirm",
            help="Não pedir confirmação interativa (adequado a scripts).",
        )

    def handle(self, *args, **options):
        username = options["username"].strip()
        if not username:
            raise CommandError("username em branco.")

        User = get_user_model()
        lookup = {User.USERNAME_FIELD: username}
        try:
            user = User._default_manager.get(**lookup)
        except User.DoesNotExist as exc:
            raise CommandError(f"Utilizador não encontrado: {username!r}.") from exc

        if options["senha"] is not None and options["interactive"]:
            raise CommandError("Use apenas uma opção: --senha ou --interactive.")

        if options["skip_confirm"]:
            self.stdout.write(self.style.WARNING("Confirmação interativa desativada (--no-input)."))
        else:
            self.stdout.write(
                f"Redefinir password para {User.USERNAME_FIELD}={user.get_username()!r}? [y/N]: ",
                ending="",
            )
            self.stdout.flush()
            confirm = sys.stdin.readline().strip().lower()
            if confirm not in ("y", "yes", "s", "sim"):
                raise CommandError("Operação cancelada.")

        if options["senha"] is not None:
            new_password = options["senha"]
            self.stdout.write(
                self.style.WARNING(
                    "Password definida via argumento: evite deixar credenciais no histórico da shell."
                )
            )
        elif options["interactive"]:
            p1 = getpass.getpass("Nova password: ")
            p2 = getpass.getpass("Repetir nova password: ")
            if p1 != p2:
                raise CommandError("As passwords não coincidem.")
            new_password = p1
        else:
            new_password = gerar_password_aleatoria()

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            raise CommandError("; ".join(e.messages)) from e

        with transaction.atomic():
            user.set_password(new_password)
            user.save(update_fields=["password"])

        self.stdout.write(self.style.SUCCESS("Password atualizada com sucesso."))
        if options["senha"] is None and not options["interactive"]:
            self.stdout.write(
                self.style.WARNING(
                    "Nova password gerada (guarde já; não será mostrada de novo nesta sessão):"
                )
            )
            self.stdout.write(new_password)
        elif options["interactive"]:
            self.stdout.write(self.style.NOTICE("Password definida via modo interativo (não repetida no ecrã)."))
