from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()

# Hosts que indicam banco local. Qualquer outro host em DATABASE_URL
# (ex: *.neon.tech) é tratado como produção/remoto e bloqueado.
LOCAL_DB_HOSTS = {"localhost", "127.0.0.1", "::1"}


class Command(BaseCommand):
    help = (
        "Cria (ou atualiza) um usuario de teste para validacao local "
        "do fluxo de gamificacao (idempotente). Somente funciona com "
        "DEBUG=True e banco de dados LOCAL."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            default="teste@lvfinance.com",
            help="E-mail do usuario de teste (padrao: teste@lvfinance.com).",
        )
        parser.add_argument(
            "--password",
            default="Teste@123456",
            help="Senha do usuario de teste (padrao: Teste@123456).",
        )
        parser.add_argument(
            "--first-name",
            default="Teste",
            help="Primeiro nome do usuario de teste.",
        )
        parser.add_argument(
            "--last-name",
            default="Gamification",
            help="Sobrenome do usuario de teste.",
        )

    def handle(self, *args, **options):
        self._refuse_if_not_local()

        email = options["email"].strip().lower()
        password = options["password"]
        extra_fields = {
            "first_name": options["first_name"],
            "last_name": options["last_name"],
        }

        if not email:
            self.stderr.write(
                self.style.ERROR("O e-mail informado esta vazio.")
            )
            return

        user, created = User.objects.get_or_create(
            email=email,
            defaults=extra_fields,
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Criado: {email}"))
        else:
            needs_update = False

            for field, value in extra_fields.items():
                if getattr(user, field, None) != value:
                    setattr(user, field, value)
                    needs_update = True

            if not user.check_password(password):
                user.set_password(password)
                needs_update = True

            if needs_update:
                user.save()
                self.stdout.write(self.style.WARNING(f"Atualizado: {email}"))
            else:
                self.stdout.write(f"Ja existe: {email}")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Login: {email} | Senha: {password}"
            )
        )

    def _refuse_if_not_local(self):
        """Bloqueia execucao contra producao (Neon) ou com DEBUG=False."""
        import os

        from django.conf import settings

        debug = getattr(settings, "DEBUG", False)
        database_url = os.getenv("DATABASE_URL", "")

        if not debug:
            raise CommandError(
                "BLOQUEADO: DJANGO_DEBUG esta False. Este comando so "
                "pode ser executado em ambiente local de desenvolvimento "
                "(DJANGO_DEBUG=True)."
            )

        if database_url:
            lowered = database_url.lower()

            if "neon.tech" in lowered or "neon.build" in lowered:
                raise CommandError(
                    "BLOQUEADO: DATABASE_URL aponta para o Neon "
                    "(producao). Use um banco local, por exemplo: "
                    "DATABASE_URL=sqlite:///db.local.sqlite3"
                )

            host = lowered.split("://", 1)[-1].split("/")[0].split("@")[-1]
            hostname = host.split(":")[0]

            if hostname not in LOCAL_DB_HOSTS and not lowered.startswith(
                ("sqlite:", "spatialite:")
            ):
                raise CommandError(
                    f"BLOQUEADO: DATABASE_URL nao parece local "
                    f"(host='{hostname}'). Somente sqlite ou localhost "
                    f"sao permitidos."
                )
