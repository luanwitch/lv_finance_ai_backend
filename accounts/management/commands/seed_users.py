import os
import secrets

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()

# Hosts que indicam banco local. Qualquer outro host em DATABASE_URL
# (ex: *.neon.tech) é tratado como produção/remoto e bloqueado.
LOCAL_DB_HOSTS = {"localhost", "127.0.0.1", "::1"}

USERS = [
    {
        "email": "admin@lvfinance.com",
        "first_name": "Admin",
        "last_name": "LV Finance",
        "is_staff": True,
        "is_superuser": True,
        "is_verified": True,
    },
    {
        "email": "teste@lvfinance.com",
        "first_name": "Teste",
        "last_name": "Usuario",
        "is_staff": False,
        "is_superuser": False,
        "is_verified": True,
    },
    {
        "email": "usuario@lvfinance.com",
        "first_name": "Usuario",
        "last_name": "Comum",
        "is_staff": False,
        "is_superuser": False,
        "is_verified": True,
    },
    {
        "email": "admin2@lvfinance.com",
        "first_name": "Admin2",
        "last_name": "LV Finance",
        "is_staff": True,
        "is_superuser": True,
        "is_verified": True,
    },
    {
        "email": "teste2@lvfinance.com",
        "first_name": "Teste2",
        "last_name": "Usuario",
        "is_staff": False,
        "is_superuser": False,
        "is_verified": True,
    },
]


class Command(BaseCommand):
    help = (
        "Cria os usuarios padrao do LV Finance AI em AMBIENTE LOCAL "
        "(idempotente). Nao deve ser executado contra producao."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=None,
            help=(
                "Senha usada para os usuarios criados. Se omitida e a env "
                "LV_SEED_PASSWORD tambem não existir, usuarios novos "
                "recebem senhas aleatorias e usuários existentes são "
                "mantidos inalterados."
            ),
        )

    def handle(self, *args, **options):
        self._refuse_if_not_local()

        env_password = os.getenv("LV_SEED_PASSWORD")
        fixed_password = options["password"] or env_password

        created_count = 0
        updated_count = 0

        for data in USERS:
            email = data["email"]
            extra_fields = {k: v for k, v in data.items() if k != "email"}

            user, created = User.objects.get_or_create(
                email=email,
                defaults=extra_fields,
            )

            if created:
                if fixed_password:
                    user.set_password(fixed_password)
                else:
                    generated = secrets.token_urlsafe(12)
                    user.set_password(generated)
                    self.stdout.write(
                        self.style.WARNING(
                            f"  [{email}] senha gerada automaticamente "
                            "(defina LV_SEED_PASSWORD para uma senha fixa)"
                        )
                    )
                user.save()
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Criado: {email}"))
            else:
                needs_update = False
                for field, value in extra_fields.items():
                    if field in ("is_staff", "is_superuser", "is_verified") and getattr(user, field) != value:
                        setattr(user, field, value)
                        needs_update = True
                    elif field in ("first_name", "last_name") and getattr(user, field, None) != value:
                        setattr(user, field, value)
                        needs_update = True

                if fixed_password and not user.check_password(fixed_password):
                    user.set_password(fixed_password)
                    needs_update = True

                if needs_update:
                    user.save()
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"  Atualizado: {email}"))
                else:
                    self.stdout.write(f"  Ja existe: {email}")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Resultado: {created_count} criados, {updated_count} atualizados, "
                f"{len(USERS) - created_count - updated_count} inalterados"
            )
        )

    def _refuse_if_not_local(self):
        """Bloqueia execucao contra producao (Neon) ou com DEBUG=False."""
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