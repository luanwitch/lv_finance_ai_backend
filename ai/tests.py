from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

CHAT_URL = "/api/ai/chat/"
ANALYZE_URL = "/api/ai/analyze/"
HEALTH_URL = "/api/ai/health/"

DUMMY_ANSWER = '{"tool": null, "data": null, "answer": "oi"}'


class ChatValidationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        cache.clear()
        self.user = User.objects.create_user(
            email="ai@example.com",
            password="strongpassword123",
        )

    def tearDown(self):
        cache.clear()

    def test_chat_requires_authentication(self):
        response = self.client.post(CHAT_URL, {"message": "oi"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_chat_empty_message_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(CHAT_URL, {"message": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chat_missing_message_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(CHAT_URL, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chat_blank_message_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(CHAT_URL, {"message": "   "})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chat_message_is_rate_limited(self):
        self.client.force_authenticate(user=self.user)

        with patch(
            "ai.services.chat_service.OllamaService.generate",
            return_value=DUMMY_ANSWER,
        ):
            for _ in range(20):
                response = self.client.post(CHAT_URL, {"message": "oi"})
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(CHAT_URL, {"message": "oi"})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class AnalyzeSecurityTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_analyze_requires_authentication(self):
        response = self.client.get(ANALYZE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AIHealthTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_health_requires_api_key(self):
        response = self.client.get(HEALTH_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_health_with_invalid_api_key(self):
        response = self.client.get(HEALTH_URL, HTTP_X_API_KEY="chave-errada")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_health_with_valid_api_key(self):
        from django.conf import settings

        if not settings.AUTHENTICATION_API_KEY:
            self.skipTest("AUTHENTICATION_API_KEY nao configurado no ambiente")

        response = self.client.get(
            HEALTH_URL,
            HTTP_X_API_KEY=settings.AUTHENTICATION_API_KEY,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "online")