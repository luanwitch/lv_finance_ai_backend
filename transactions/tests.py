from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from categories.models import Category
from transactions.models import Transaction

User = get_user_model()


class TransactionTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/transactions/transactions/"
        self.user = User.objects.create_user(
            email="test@example.com",
            password="strongpassword123",
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(
            user=self.user,
            name="Alimentação",
            icon="🍽️",
            type="expense",
        )

    def _create_transaction(self, **overrides):
        data = {
            "title": "Almoço",
            "amount": "45.90",
            "category": "alimentacao",
            "category_fk": self.category.id,
            "type": "expense",
            "date": str(timezone.now().date()),
            "description": "Almoço no restaurante",
        }
        data.update(overrides)
        return self.client.post(self.url, data, format="json")

    def test_create_transaction(self):
        response = self._create_transaction()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Transaction.objects.first().title, "Almoço")

    def test_list_transactions(self):
        self._create_transaction()
        self._create_transaction(title="Jantar", amount="60.00")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_only_own_transactions(self):
        other_user = User.objects.create_user(
            email="other@example.com", password="password123"
        )
        Transaction.objects.create(
            user=other_user,
            title="Other",
            amount=Decimal("10.00"),
            category="outros",
            type="expense",
            date=timezone.now().date(),
        )
        self._create_transaction()
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)

    def test_delete_transaction(self):
        self._create_transaction()
        tx_id = Transaction.objects.first().id
        response = self.client.delete(f"{self.url}{tx_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_create_transaction_invalid_amount(self):
        response = self._create_transaction(amount="-10")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_summary(self):
        Transaction.objects.create(
            user=self.user,
            title="Salary",
            amount=Decimal("5000.00"),
            category="salario",
            type="income",
            date=timezone.now().date(),
        )
        self._create_transaction()
        response = self.client.get(f"{self.url}summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("balance", response.data)
        self.assertIn("income", response.data)
        self.assertIn("expense", response.data)

    def test_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TransactionCategoryFKTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/transactions/transactions/"
        self.user = User.objects.create_user(
            email="test@example.com", password="strongpassword123"
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(
            user=self.user,
            name="Transporte",
            icon="🚗",
            type="expense",
        )

    def test_create_with_category_fk(self):
        data = {
            "title": "Uber",
            "amount": "25.00",
            "category_fk": self.category.id,
            "type": "expense",
            "date": str(timezone.now().date()),
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["category_fk"], self.category.id)
        self.assertIn("category_detail", response.data)
        self.assertEqual(
            response.data["category_detail"]["name"], "Transporte"
        )

    def test_category_detail_in_list(self):
        Transaction.objects.create(
            user=self.user,
            title="Test",
            amount=Decimal("10.00"),
            category="teste",
            type="expense",
            date=timezone.now().date(),
            category_fk=self.category,
        )
        response = self.client.get(self.url)
        tx = response.data[0]
        self.assertIn("category_detail", tx)
        self.assertEqual(tx["category_detail"]["name"], "Transporte")
