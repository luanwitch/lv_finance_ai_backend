from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

USERS = [
    {
        "email": "admin@lvfinance.com",
        "password": "Admin@123456",
        "first_name": "Admin",
        "last_name": "LV Finance",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "email": "teste@lvfinance.com",
        "password": "Teste@123456",
        "first_name": "Teste",
        "last_name": "Usuario",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "email": "usuario@lvfinance.com",
        "password": "Usuario@123456",
        "first_name": "Usuario",
        "last_name": "Comum",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "email": "admin2@lvfinance.com",
        "password": "Admin2@123456",
        "first_name": "Admin2",
        "last_name": "LV Finance",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "email": "teste2@lvfinance.com",
        "password": "Teste2@123456",
        "first_name": "Teste2",
        "last_name": "Usuario",
        "is_staff": False,
        "is_superuser": False,
    },
]


class Command(BaseCommand):
    help = "Cria os usuarios padrao do LV Finance AI (idempotente)"

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for data in USERS:
            email = data["email"]
            password = data["password"]
            extra_fields = {k: v for k, v in data.items() if k != "password"}

            user, created = User.objects.get_or_create(
                email=email,
                defaults=extra_fields,
            )

            if created:
                user.set_password(password)
                user.save()
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  Criado: {email}")
                )
            else:
                needs_update = False
                for field, value in extra_fields.items():
                    if field in ("is_staff", "is_superuser") and getattr(user, field) != value:
                        setattr(user, field, value)
                        needs_update = True
                    elif field in ("first_name", "last_name") and getattr(user, field, None) != value:
                        setattr(user, field, value)
                        needs_update = True

                if not user.check_password(password):
                    user.set_password(password)
                    needs_update = True

                if needs_update:
                    user.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  Atualizado: {email}")
                    )
                else:
                    self.stdout.write(f"  Ja existe: {email}")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Resultado: {created_count} criados, {updated_count} atualizados, "
                f"{len(USERS) - created_count - updated_count} inalterados"
            )
        )
