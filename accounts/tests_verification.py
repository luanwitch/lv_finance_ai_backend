import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import EmailVerificationToken
from .services import _token_hash

User = get_user_model()

REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/login/"
VERIFY_URL = "/api/auth/verify-email/"
RESEND_URL = "/api/auth/resend-verification/"

VALID_DATA = {
    "first_name": "Teste",
    "last_name": "User",
    "email": "test@example.com",
    "password": "strongpassword123",
}

TOKEN_RE = re.compile(r"verify-email\?token=(?P<token>[A-Za-z0-9_-]+)")


def extract_token_from_email(outbox_item):
    match = TOKEN_RE.search(outbox_item.body)
    if match is None:
        match = TOKEN_RE.search(outbox_item.alternatives[0][0])
    return match.group("token") if match else None


class RegisterEmailVerificationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        mail.outbox = []

    def test_register_creates_unverified_user(self):
        response = self.client.post(REGISTER_URL, VALID_DATA)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email=VALID_DATA["email"])
        self.assertFalse(user.is_verified)

    def test_register_generates_token_and_sends_email(self):
        response = self.client.post(REGISTER_URL, VALID_DATA)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email=VALID_DATA["email"])
        token = EmailVerificationToken.objects.get(user=user)
        self.assertIsNone(token.used_at)
        self.assertGreater(token.expires_at, timezone.now())

        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.to, [VALID_DATA["email"]])
        self.assertIn("Confirme seu e-mail", sent.subject)

        raw_token = extract_token_from_email(sent)
        self.assertIsNotNone(raw_token)
        self.assertEqual(_token_hash(raw_token), token.token_hash)

    def test_email_exposes_safety_information(self):
        self.client.post(REGISTER_URL, VALID_DATA)
        sent = mail.outbox[0]
        body = sent.body
        html_body = sent.alternatives[0][0]
        self.assertIn("LV Finance AI", body)
        self.assertIn("criada com sucesso", body)
        self.assertIn("horas", body)
        self.assertIn("ignore este e-mail", body)
        self.assertIn("Confirmar e-mail", html_body)

    def test_register_reverts_user_on_email_failure(self):
        from unittest.mock import patch

        with patch("accounts.services.send_mail", side_effect=Exception("SMTP down")):
            response = self.client.post(REGISTER_URL, VALID_DATA)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(
            User.objects.filter(email=VALID_DATA["email"]).exists(),
            "User should be deleted when email sending fails",
        )
        self.assertEqual(len(mail.outbox), 0)


class VerifyEmailTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        mail.outbox = []
        self.client.post(REGISTER_URL, VALID_DATA)
        self.user = User.objects.get(email=VALID_DATA["email"])
        self.raw_token = extract_token_from_email(mail.outbox[0])

    def test_valid_token_confirms_user(self):
        response = self.client.post(VERIFY_URL, {"token": self.raw_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)

        token = EmailVerificationToken.objects.get(user=self.user)
        self.assertIsNotNone(token.used_at)

    def test_invalid_token_is_rejected(self):
        response = self.client.post(VERIFY_URL, {"token": "token-que-nao-existe"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "invalid_token")

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)

    def test_expired_token_is_rejected(self):
        raw_token = "token-expirado-de-teste"
        EmailVerificationToken.objects.filter(user=self.user).delete()
        EmailVerificationToken.objects.create(
            user=self.user,
            token_hash=_token_hash(raw_token),
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        response = self.client.post(VERIFY_URL, {"token": raw_token})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "token_expired")

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)

    def test_token_cannot_be_reused(self):
        first = self.client.post(VERIFY_URL, {"token": self.raw_token})
        self.assertEqual(first.data["status"], "success")

        second = self.client.post(VERIFY_URL, {"token": self.raw_token})
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(second.data["status"], "already_verified")

    def test_already_verified_user_gets_adequate_response(self):
        self.user.is_verified = True
        self.user.save(update_fields=("is_verified",))

        response = self.client.post(VERIFY_URL, {"token": self.raw_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "already_verified")

    def test_missing_token_returns_400(self):
        response = self.client.post(VERIFY_URL, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginEmailVerificationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = LOGIN_URL

    def test_unverified_user_cannot_login(self):
        user = User.objects.create_user(
            email="unverified@example.com",
            password="strongpassword123",
            is_verified=False,
        )
        self.assertFalse(user.is_verified)

        response = self.client.post(
            self.url,
            {"email": "unverified@example.com", "password": "strongpassword123"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "email_not_verified")
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_verified_user_can_login(self):
        User.objects.create_user(
            email="verified@example.com",
            password="strongpassword123",
            is_verified=True,
        )
        response = self.client.post(
            self.url,
            {"email": "verified@example.com", "password": "strongpassword123"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


class ResendVerificationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        mail.outbox = []

    def register_and_extract_token(self):
        self.client.post(REGISTER_URL, VALID_DATA)
        return extract_token_from_email(mail.outbox[0])

    def test_resend_generates_new_token_and_sends_email(self):
        old_token = self.register_and_extract_token()
        self.assertEqual(len(mail.outbox), 1)

        response = self.client.post(
            RESEND_URL, {"email": VALID_DATA["email"]}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = User.objects.get(email=VALID_DATA["email"])
        active_tokens = EmailVerificationToken.objects.filter(
            user=user, used_at__isnull=True
        )
        self.assertEqual(active_tokens.count(), 1)

        self.assertEqual(len(mail.outbox), 2)
        new_token = extract_token_from_email(mail.outbox[1])
        self.assertIsNotNone(new_token)
        self.assertNotEqual(new_token, old_token)

        verify_response = self.client.post(VERIFY_URL, {"token": new_token})
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertEqual(verify_response.data["status"], "success")

        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    def test_old_token_is_invalidated_after_resend(self):
        old_token = self.register_and_extract_token()

        self.client.post(RESEND_URL, {"email": VALID_DATA["email"]})

        response = self.client.post(VERIFY_URL, {"token": old_token})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "invalid_token")

        user = User.objects.get(email=VALID_DATA["email"])
        self.assertFalse(user.is_verified)

    def test_resend_nonexistent_email_does_not_reveal_info(self):
        response = self.client.post(
            RESEND_URL, {"email": "nao-existe@example.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Se o e-mail estiver cadastrado", response.data["detail"])
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_verified_email_sends_nothing(self):
        User.objects.create_user(
            email=VALID_DATA["email"],
            password=VALID_DATA["password"],
            is_verified=True,
        )

        response = self.client.post(
            RESEND_URL, {"email": VALID_DATA["email"]}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_missing_email_returns_400(self):
        response = self.client.post(RESEND_URL, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ResendVerificationRateLimitTests(TestCase):

    RESEND_LIMIT = 5

    def setUp(self):
        self.client = APIClient()
        cache.clear()
        self.client.post(
            REGISTER_URL,
            {
                "first_name": "Teste",
                "last_name": "User",
                "email": "test@example.com",
                "password": "strongpassword123",
            },
        )

    def tearDown(self):
        cache.clear()

    def test_resend_is_rate_limited(self):
        for _ in range(self.RESEND_LIMIT):
            response = self.client.post(
                RESEND_URL, {"email": "test@example.com"}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            RESEND_URL, {"email": "test@example.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class EmailVerificationEndToEndTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        mail.outbox = []

    def _register(self):
        response = self.client.post(REGISTER_URL, VALID_DATA)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def _extract_token(self):
        return extract_token_from_email(mail.outbox[0])

    def test_full_registration_flow(self):
        self._register()

        user = User.objects.get(email=VALID_DATA["email"])
        self.assertFalse(user.is_verified)

        token = EmailVerificationToken.objects.get(user=user)
        self.assertIsNone(token.used_at)
        self.assertGreater(token.expires_at, timezone.now())

        self.assertEqual(len(mail.outbox), 1)
        raw_token = self._extract_token()
        self.assertIsNotNone(raw_token)

        login_before = self.client.post(
            LOGIN_URL,
            {"email": VALID_DATA["email"], "password": VALID_DATA["password"]},
        )
        self.assertEqual(login_before.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(login_before.data["code"], "email_not_verified")

        verify = self.client.post(VERIFY_URL, {"token": raw_token})
        self.assertEqual(verify.status_code, status.HTTP_200_OK)
        self.assertEqual(verify.data["status"], "success")

        user.refresh_from_db()
        self.assertTrue(user.is_verified)

        token.refresh_from_db()
        self.assertIsNotNone(token.used_at)

        login_after = self.client.post(
            LOGIN_URL,
            {"email": VALID_DATA["email"], "password": VALID_DATA["password"]},
        )
        self.assertEqual(login_after.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_after.data)
        self.assertIn("refresh", login_after.data)

    def test_expired_token_flow_requires_resend(self):
        self._register()
        user = User.objects.get(email=VALID_DATA["email"])
        raw_token = self._extract_token()

        EmailVerificationToken.objects.filter(user=user).delete()
        EmailVerificationToken.objects.create(
            user=user,
            token_hash=_token_hash(raw_token),
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        expired = self.client.post(VERIFY_URL, {"token": raw_token})
        self.assertEqual(expired.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(expired.data["status"], "token_expired")

        user.refresh_from_db()
        self.assertFalse(user.is_verified)

        login = self.client.post(
            LOGIN_URL,
            {"email": VALID_DATA["email"], "password": VALID_DATA["password"]},
        )
        self.assertEqual(login.status_code, status.HTTP_403_FORBIDDEN)

        resend = self.client.post(RESEND_URL, {"email": VALID_DATA["email"]})
        self.assertEqual(resend.status_code, status.HTTP_200_OK)

        self.assertEqual(len(mail.outbox), 2)
        new_token = extract_token_from_email(mail.outbox[1])
        self.assertIsNotNone(new_token)
        self.assertNotEqual(new_token, raw_token)

        verify = self.client.post(VERIFY_URL, {"token": new_token})
        self.assertEqual(verify.status_code, status.HTTP_200_OK)
        self.assertEqual(verify.data["status"], "success")

        user.refresh_from_db()
        self.assertTrue(user.is_verified)

        login = self.client.post(
            LOGIN_URL,
            {"email": VALID_DATA["email"], "password": VALID_DATA["password"]},
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)