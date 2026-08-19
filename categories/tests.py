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


class CategoryIsolationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/categories/"
        self.user_a = User.objects.create_user(
            email="user_a@example.com", password="password123"
        )
        self.user_b = User.objects.create_user(
            email="user_b@example.com", password="password123"
        )
        self.cat_a = Category.objects.create(
            user=self.user_a, name="Category A", icon="📁", type="expense"
        )
        self.cat_b = Category.objects.create(
            user=self.user_b, name="Category B", icon="📁", type="expense"
        )

    def test_user_a_cannot_see_user_b_categories(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.cat_a.id)

    def test_user_b_cannot_see_user_a_categories(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.cat_b.id)

    def test_user_a_cannot_get_user_b_category_by_id(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(f"{self.url}{self.cat_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_b_cannot_get_user_a_category_by_id(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get(f"{self.url}{self.cat_a.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_cannot_delete_user_b_category(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.delete(f"{self.url}{self.cat_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Category.objects.filter(id=self.cat_b.id).exists())

    def test_user_b_cannot_delete_user_a_category(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.delete(f"{self.url}{self.cat_a.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Category.objects.filter(id=self.cat_a.id).exists())

    def test_user_a_cannot_update_user_b_category(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.patch(
            f"{self.url}{self.cat_b.id}/",
            {"name": "Hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.cat_b.refresh_from_db()
        self.assertEqual(self.cat_b.name, "Category B")

    def test_user_b_cannot_update_user_a_category(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.patch(
            f"{self.url}{self.cat_a.id}/",
            {"name": "Hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.cat_a.refresh_from_db()
        self.assertEqual(self.cat_a.name, "Category A")

    def test_create_category_associates_to_authenticated_user(self):
        self.client.force_authenticate(user=self.user_a)
        data = {
            "name": "New Category",
            "icon": "🆕",
            "type": "income",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cat = Category.objects.get(id=response.data["id"])
        self.assertEqual(cat.user, self.user_a)
        self.assertNotEqual(cat.user, self.user_b)
