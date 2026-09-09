import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import PasswordResetToken
from .services import _token_hash

User = get_user_model()

REQUEST_URL = "/api/auth/password-reset/request/"
CONFIRM_URL = "/api/auth/password-reset/confirm/"
CHANGE_URL = "/api/auth/change-password/"
LOGIN_URL = "/api/auth/login/"

VALID_PASSWORD = "novasenhaforte123"

RESET_TOKEN_RE = re.compile(r"reset-password\?token=(?P<token>[A-Za-z0-9_-]+)")


def extract_reset_token(outbox_item):
    match = RESET_TOKEN_RE.search(outbox_item.body)
    if match is None:
        match = RESET_TOKEN_RE.search(outbox_item.alternatives[0][0])
    return match.group("token") if match else None


class RequestPasswordResetTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        cache.clear()
        mail.outbox = []
        self.user = User.objects.create_user(
            email="reset@example.com",
            password="senhaatual123",
        )

    def tearDown(self):
        cache.clear()

    def test_request_creates_token_and_sends_email(self):
        response = self.client.post(REQUEST_URL, {"email": self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token = PasswordResetToken.objects.get(user=self.user)
        self.assertIsNone(token.used_at)
        self.assertGreater(token.expires_at, timezone.now())

        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.to, [self.user.email])
        self.assertIn("Redefinição", sent.subject)

        raw_token = extract_reset_token(sent)
        self.assertIsNotNone(raw_token)
        self.assertEqual(_token_hash(raw_token), token.token_hash)

    def test_request_nonexistent_email_does_not_reveal_info(self):
        response = self.client.post(
            REQUEST_URL, {"email": "nao-existe@example.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Se o e-mail estiver cadastrado", response.data["detail"])
        self.assertEqual(len(mail.outbox), 0)

    def test_request_missing_email_returns_400(self):
        response = self.client.post(REQUEST_URL, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_invalid_email_returns_400(self):
        response = self.client.post(REQUEST_URL, {"email": "invalido"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_invalidates_previous_active_tokens(self):
        self.client.post(REQUEST_URL, {"email": self.user.email})
        self.client.post(REQUEST_URL, {"email": self.user.email})

        active = PasswordResetToken.objects.filter(
            user=self.user, used_at__isnull=True
        )
        self.assertEqual(active.count(), 1)


class RequestPasswordResetRateLimitTests(TestCase):

    RESET_LIMIT = 5

    def setUp(self):
        self.client = APIClient()
        cache.clear()
        self.user = User.objects.create_user(
            email="reset@example.com",
            password="senhaatual123",
        )

    def tearDown(self):
        cache.clear()

    def test_request_is_rate_limited(self):
        for _ in range(self.RESET_LIMIT):
            response = self.client.post(
                REQUEST_URL, {"email": self.user.email}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            REQUEST_URL, {"email": self.user.email}
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class PasswordResetConfirmTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        cache.clear()
        mail.outbox = []
        self.user = User.objects.create_user(
            email="reset@example.com",
            password="senhaatual123",
            is_verified=True,
        )
        self.client.post(REQUEST_URL, {"email": self.user.email})
        self.raw_token = extract_reset_token(mail.outbox[0])

    def tearDown(self):
        cache.clear()

    def test_valid_token_resets_password_and_marks_used(self):
        response = self.client.post(
            CONFIRM_URL,
            {"token": self.raw_token, "password": VALID_PASSWORD},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(VALID_PASSWORD))

        token = PasswordResetToken.objects.get(user=self.user)
        self.assertIsNotNone(token.used_at)

    def test_new_password_works_on_login(self):
        self.client.post(
            CONFIRM_URL,
            {"token": self.raw_token, "password": VALID_PASSWORD},
        )

        login_response = self.client.post(
            LOGIN_URL,
            {"email": self.user.email, "password": VALID_PASSWORD},
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)

    def test_token_cannot_be_reused(self):
        first = self.client.post(
            CONFIRM_URL,
            {"token": self.raw_token, "password": VALID_PASSWORD},
        )
        self.assertEqual(first.data["status"], "success")

        second = self.client.post(
            CONFIRM_URL,
            {"token": self.raw_token, "password": "outrasenha123"},
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(second.data["status"], "invalid_token")

    def test_invalid_token_returns_400(self):
        response = self.client.post(
            CONFIRM_URL,
            {"token": "token-inexistente", "password": VALID_PASSWORD},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "invalid_token")

    def test_expired_token_returns_400(self):
        PasswordResetToken.objects.filter(user=self.user).delete()
        PasswordResetToken.objects.create(
            user=self.user,
            token_hash=_token_hash("token-expirado"),
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        response = self.client.post(
            CONFIRM_URL,
            {"token": "token-expirado", "password": VALID_PASSWORD},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "token_expired")

    def test_missing_token_returns_400(self):
        response = self.client.post(CONFIRM_URL, {"password": VALID_PASSWORD})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_is_rejected(self):
        response = self.client.post(
            CONFIRM_URL,
            {"token": self.raw_token, "password": "123"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("senhaatual123"))


class ChangePasswordTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.password = "senhaatual123"
        self.user = User.objects.create_user(
            email="change@example.com",
            password=self.password,
        )

    def test_requires_authentication(self):
        response = self.client.post(
            CHANGE_URL,
            {
                "current_password": self.password,
                "new_password": VALID_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_success_changes_password(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            CHANGE_URL,
            {
                "current_password": self.password,
                "new_password": VALID_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(VALID_PASSWORD))
        self.assertFalse(self.user.check_password(self.password))

    def test_wrong_current_password_is_rejected(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            CHANGE_URL,
            {
                "current_password": "senhaerrada99",
                "new_password": VALID_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("current_password", response.data)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))

    def test_short_new_password_is_rejected(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            CHANGE_URL,
            {
                "current_password": self.password,
                "new_password": "123",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)