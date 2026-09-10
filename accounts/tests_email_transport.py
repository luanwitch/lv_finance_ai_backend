import logging
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from httpx import ConnectError
from rest_framework import status
from rest_framework.test import APIClient

from .email_service import EmailSendError, send_email

User = get_user_model()

REGISTER_URL = "/api/auth/register/"
RESEND_URL = "/api/auth/resend-verification/"
RESET_REQUEST_URL = "/api/auth/password-reset/request/"


class FakeResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code


@override_settings(RESEND_API_KEY="sk_test_placeholder")
class HttpEmailTransportEndpointTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        mail.outbox = []
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_resend_uses_http_provider_when_api_key_is_set(self):
        user = User.objects.create_user(
            email="http@example.com",
            password="strongpassword123",
            is_verified=False,
        )

        with patch(
            "accounts.email_service.httpx.post", return_value=FakeResponse()
        ) as mock_post:
            response = self.client.post(RESEND_URL, {"email": user.email})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mock_post.call_count, 1)
        kwargs = mock_post.call_args.kwargs
        payload = kwargs["json"]
        self.assertEqual(payload["to"], [user.email])
        self.assertEqual(payload["subject"], "Confirme seu e-mail - LV Finance AI")
        self.assertIn("text", payload)
        self.assertIn("html", payload)
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer sk_test_placeholder")
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_returns_500_when_http_provider_fails(self):
        user = User.objects.create_user(
            email="httpfail@example.com",
            password="strongpassword123",
            is_verified=False,
        )

        with patch(
            "accounts.email_service.httpx.post",
            side_effect=ConnectError("network is unreachable"),
        ):
            response = self.client.post(RESEND_URL, {"email": user.email})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn(
            "Nao foi possivel enviar o e-mail", response.data["detail"]
        )

    def test_resend_returns_500_when_http_provider_rejects(self):
        user = User.objects.create_user(
            email="httpreject@example.com",
            password="strongpassword123",
            is_verified=False,
        )

        with patch(
            "accounts.email_service.httpx.post", return_value=FakeResponse(422)
        ):
            response = self.client.post(RESEND_URL, {"email": user.email})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_password_reset_uses_http_provider_success(self):
        user = User.objects.create_user(
            email="httpreset@example.com",
            password="strongpassword123",
            is_verified=True,
        )

        with patch(
            "accounts.email_service.httpx.post", return_value=FakeResponse()
        ) as mock_post:
            response = self.client.post(
                RESET_REQUEST_URL, {"email": user.email}
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["to"], [user.email])
        self.assertEqual(payload["subject"], "Redefinição de senha - LV Finance AI")
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_returns_500_when_http_provider_fails(self):
        user = User.objects.create_user(
            email="httpresetfail@example.com",
            password="strongpassword123",
        )

        with patch(
            "accounts.email_service.httpx.post",
            side_effect=ConnectError("network is unreachable"),
        ):
            response = self.client.post(
                RESET_REQUEST_URL, {"email": user.email}
            )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn(
            "Nao foi possivel enviar o e-mail", response.data["detail"]
        )

    def test_register_returns_500_and_keeps_no_user_when_http_provider_fails(self):
        data = {
            "first_name": "Teste",
            "last_name": "User",
            "email": "httpreg@example.com",
            "password": "strongpassword123",
        }

        with patch(
            "accounts.email_service.httpx.post",
            side_effect=ConnectError("network is unreachable"),
        ):
            response = self.client.post(REGISTER_URL, data)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(User.objects.filter(email=data["email"]).exists())


@override_settings(RESEND_API_KEY="sk_secret_test_value")
class HttpEmailTransportNoSecretsTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_failure_logs_do_not_contain_secrets_or_tokens(self):
        user = User.objects.create_user(
            email="secret@example.com",
            password="strongpassword123",
            is_verified=False,
        )

        records = []

        class CaptureHandler(logging.Handler):
            def emit(self, record):
                records.append(self.format(record))

        handler = CaptureHandler()
        target_logger = logging.getLogger("accounts")
        target_logger.addHandler(handler)
        try:
            with patch(
                "accounts.email_service.httpx.post",
                side_effect=ConnectError("network is unreachable"),
            ):
                response = self.client.post(RESEND_URL, {"email": user.email})
        finally:
            target_logger.removeHandler(handler)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        joined = "\n".join(records)
        self.assertNotIn("sk_secret_test_value", joined)
        self.assertNotIn("Bearer", joined)
        self.assertNotIn("verify-email", joined)


class EmailServiceUnitTests(TestCase):

    def setUp(self):
        mail.outbox = []

    @override_settings(RESEND_API_KEY="")
    def test_fallback_uses_django_backend(self):
        send_email(
            subject="Assunto",
            message="Corpo texto",
            html_message="<b>Corpo html</b>",
            recipient_list=["fallback@example.com"],
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Assunto")

    @override_settings(RESEND_API_KEY="")
    def test_fallback_never_calls_http(self):
        with patch("accounts.email_service.httpx.post") as mock_post:
            send_email(
                subject="s",
                message="m",
                html_message="<b>m</b>",
                recipient_list=["fallback@example.com"],
            )
        mock_post.assert_not_called()

    @override_settings(RESEND_API_KEY="sk_unit_test")
    def test_http_success(self):
        with patch(
            "accounts.email_service.httpx.post", return_value=FakeResponse()
        ) as mock_post:
            send_email(
                subject="s",
                message="m",
                html_message="<b>m</b>",
                recipient_list=["httpunit@example.com"],
            )
        mock_post.assert_called_once()
        self.assertIn(
            "httpunit@example.com", mock_post.call_args.kwargs["json"]["to"]
        )

    @override_settings(RESEND_API_KEY="sk_unit_test")
    def test_http_network_error_raises_email_send_error(self):
        with (
            patch(
                "accounts.email_service.httpx.post",
                side_effect=ConnectError("network is unreachable"),
            ),
            self.assertRaises(EmailSendError),
        ):
            send_email(
                subject="s",
                message="m",
                html_message="<b>m</b>",
                recipient_list=["httpunit@example.com"],
            )

    @override_settings(RESEND_API_KEY="sk_unit_test")
    def test_http_5xx_raises_email_send_error(self):
        with (
            patch(
                "accounts.email_service.httpx.post", return_value=FakeResponse(500)
            ),
            self.assertRaises(EmailSendError),
        ):
            send_email(
                subject="s",
                message="m",
                html_message="<b>m</b>",
                recipient_list=["httpunit@example.com"],
            )