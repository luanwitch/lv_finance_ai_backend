from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from categories.models import Category

User = get_user_model()


class CategoryTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/categories/"
        self.user = User.objects.create_user(
            email="test@example.com",
            password="strongpassword123",
        )
        self.client.force_authenticate(user=self.user)

    def _create_category(self, **overrides):
        data = {
            "name": "Alimentação",
            "icon": "🍽️",
            "color": "#FF6B6B",
            "type": "expense",
        }
        data.update(overrides)
        return self.client.post(self.url, data, format="json")

    def test_create_category(self):
        response = self._create_category()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)
        self.assertIn("icon", response.data)

    def test_list_categories(self):
        self._create_category(name="Transporte", icon="🚗")
        self._create_category(name="Moradia", icon="🏠")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_only_own_categories(self):
        other_user = User.objects.create_user(
            email="other@example.com", password="password123"
        )
        Category.objects.create(
            user=other_user, name="Other", icon="📦", type="expense"
        )
        self._create_category()
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)

    def test_update_category(self):
        cat = self._create_category()
        cat_id = cat.data["id"]
        response = self.client.patch(
            f"{self.url}{cat_id}/",
            {"name": "Updated"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated")

    def test_delete_category(self):
        cat = self._create_category()
        cat_id = cat.data["id"]
        response = self.client.delete(f"{self.url}{cat_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)

    def test_icon_field_present(self):
        response = self._create_category()
        self.assertIn("icon", response.data)
        self.assertEqual(response.data["icon"], "🍽️")
