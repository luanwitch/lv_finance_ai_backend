from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import EmailVerificationToken, PasswordResetToken


class Command(BaseCommand):
    help = (
        "Remove tokens de verificacao de e-mail e de redefinicao de senha "
        "expirados. Tokens usados (used_at preenchido) tambem sao removidos."
    )

    def handle(self, *args, **options):
        now = timezone.now()

        expired_verification = EmailVerificationToken.objects.filter(
            expires_at__lte=now
        ).delete()[0]
        expired_password = PasswordResetToken.objects.filter(
            expires_at__lte=now
        ).delete()[0]

        used_verification = EmailVerificationToken.objects.filter(
            used_at__isnull=False
        ).delete()[0]
        used_password = PasswordResetToken.objects.filter(
            used_at__isnull=False
        ).delete()[0]

        self.stdout.write(
            self.style.SUCCESS(
                "Tokens removidos: "
                f"{expired_verification + used_verification} de verificacao "
                f"({expired_verification} expirados, {used_verification} usados), "
                f"{expired_password + used_password} de senha "
                f"({expired_password} expirados, {used_password} usados)."
            )
        )