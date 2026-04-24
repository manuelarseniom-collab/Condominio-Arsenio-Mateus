from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from usuarios.user_audit import (
    CABECALHO_TXT,
    escrever_csv,
    escrever_txt,
    formatar_linha_texto,
    iter_linhas_auditoria,
    resumo_utilizadores,
)


class Command(BaseCommand):
    help = (
        "Lista utilizadores para auditoria interna: sem passwords, sem hashes, "
        "com indicador de password utilizável (has_usable_password)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--export",
            metavar="CAMINHO",
            help="Exportar para ficheiro .csv ou .txt (consoante a extensão).",
        )
        parser.add_argument(
            "--silent",
            action="store_true",
            help="Não imprimir a tabela no ecrã (mantém resumo e mensagens de export).",
        )

    def handle(self, *args, **options):
        linhas = list(iter_linhas_auditoria())
        total, superusers, staff, ativos = resumo_utilizadores(linhas)

        if not options["silent"]:
            self.stdout.write(CABECALHO_TXT)
            self.stdout.write("-" * len(CABECALHO_TXT))
            for linha in linhas:
                self.stdout.write(formatar_linha_texto(linha=linha))

        self.stdout.write("")
        self.stdout.write(
            self.style.NOTICE(
                f"Total: {total} | Superutilizadores: {superusers} | Staff: {staff} | Ativos: {ativos}"
            )
        )

        export = options.get("export")
        if not export:
            return

        path = Path(export)
        suf = path.suffix.lower()
        if suf == ".csv":
            escrever_csv(str(path), linhas)
            self.stdout.write(self.style.SUCCESS(f"Exportado CSV: {path.resolve()}"))
        elif suf == ".txt":
            escrever_txt(str(path), linhas)
            self.stdout.write(self.style.SUCCESS(f"Exportado TXT: {path.resolve()}"))
        else:
            raise CommandError("Em --export use extensão .csv ou .txt.")
