from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class RegisterTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/auth/register/"

    def test_register_success(self):
        data = {
            "first_name": "Teste",
            "last_name": "User",
            "email": "test@example.com",
            "password": "strongpassword123",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

    def test_register_short_password(self):
        data = {
            "first_name": "Teste",
            "email": "test@example.com",
            "password": "short",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        User.objects.create_user(
            email="test@example.com", password="strongpassword123"
        )
        data = {
            "first_name": "Teste",
            "email": "test@example.com",
            "password": "anotherpassword123",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/auth/login/"
        self.user = User.objects.create_user(
            email="test@example.com",
            password="strongpassword123",
            first_name="Teste",
        )

    def test_login_success(self):
        data = {
            "email": "test@example.com",
            "password": "strongpassword123",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password(self):
        data = {
            "email": "test@example.com",
            "password": "wrongpassword",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        data = {
            "email": "nobody@example.com",
            "password": "anypassword",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_empty_body_returns_400(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_password_returns_400(self):
        response = self.client.post(self.url, {"email": "test@example.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_email_returns_400(self):
        response = self.client.post(self.url, {"password": "strongpassword123"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_never_returns_500(self):
        for data in [
            {},
            {"email": "test@example.com"},
            {"password": "strongpassword123"},
            {"email": "test@example.com", "password": "wrong"},
            {"email": "nobody@example.com", "password": "x"},
        ]:
            response = self.client.post(self.url, data)
            self.assertNotEqual(
                response.status_code,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"500 on payload {data}",
            )


class ProfileTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/auth/profile/"
        self.user = User.objects.create_user(
            email="test@example.com",
            password="strongpassword123",
            first_name="Teste",
            last_name="User",
        )
        self.client.force_authenticate(user=self.user)

    def test_profile_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["first_name"], "Teste")

    def test_profile_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MeTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/auth/me/"
        self.user = User.objects.create_user(
            email="test@example.com",
            password="strongpassword123",
            first_name="Teste",
            last_name="User",
        )
        self.client.force_authenticate(user=self.user)

    def test_me_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")
