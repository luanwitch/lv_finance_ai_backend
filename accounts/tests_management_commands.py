from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from .models import EmailVerificationToken, PasswordResetToken
from .services import _token_hash

User = get_user_model()


class ClearExpiredTokensTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="cleanup@example.com",
            password="strongpassword123",
        )

        self.expired_verification = EmailVerificationToken.objects.create(
            user=self.user,
            token_hash=_token_hash("token-expirado-verify"),
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        self.active_verification = EmailVerificationToken.objects.create(
            user=self.user,
            token_hash=_token_hash("token-ativo-verify"),
            expires_at=timezone.now() + timedelta(hours=1),
        )

        self.used_verification = EmailVerificationToken.objects.create(
            user=self.user,
            token_hash=_token_hash("token-usado-verify"),
            expires_at=timezone.now() + timedelta(hours=1),
            used_at=timezone.now(),
        )

        self.expired_password = PasswordResetToken.objects.create(
            user=self.user,
            token_hash=_token_hash("token-expirado-password"),
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        self.active_password = PasswordResetToken.objects.create(
            user=self.user,
            token_hash=_token_hash("token-ativo-password"),
            expires_at=timezone.now() + timedelta(hours=1),
        )

        self.used_password = PasswordResetToken.objects.create(
            user=self.user,
            token_hash=_token_hash("token-usado-password"),
            expires_at=timezone.now() + timedelta(hours=1),
            used_at=timezone.now(),
        )

    def test_removes_only_expired_and_used_tokens(self):
        call_command("clear_expired_tokens", verbosity=0)

        self.assertFalse(
            EmailVerificationToken.objects.filter(
                pk=self.expired_verification.pk
            ).exists()
        )
        self.assertFalse(
            EmailVerificationToken.objects.filter(pk=self.used_verification.pk).exists()
        )
        self.assertTrue(
            EmailVerificationToken.objects.filter(pk=self.active_verification.pk).exists()
        )

        self.assertFalse(
            PasswordResetToken.objects.filter(pk=self.expired_password.pk).exists()
        )
        self.assertFalse(
            PasswordResetToken.objects.filter(pk=self.used_password.pk).exists()
        )
        self.assertTrue(
            PasswordResetToken.objects.filter(pk=self.active_password.pk).exists()
        )

    def test_idempotent(self):
        call_command("clear_expired_tokens", verbosity=0)
        call_command("clear_expired_tokens", verbosity=0)

        self.assertTrue(
            EmailVerificationToken.objects.filter(pk=self.active_verification.pk).exists()
        )
        self.assertTrue(
            PasswordResetToken.objects.filter(pk=self.active_password.pk).exists()
        )