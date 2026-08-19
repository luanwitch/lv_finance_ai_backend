from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from goals.models import Goal

User = get_user_model()


class GoalTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/goals/"
        self.user = User.objects.create_user(
            email="test@example.com",
            password="strongpassword123",
        )
        self.client.force_authenticate(user=self.user)

    def _create_goal(self, **overrides):
        data = {
            "title": "Viagem Europa",
            "target_amount": "15000.00",
            "description": "Férias na Europa",
        }
        data.update(overrides)
        return self.client.post(self.url, data, format="json")

    def test_create_goal(self):
        response = self._create_goal()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Goal.objects.count(), 1)
        self.assertEqual(response.data["title"], "Viagem Europa")

    def test_list_goals(self):
        self._create_goal(title="Meta 1")
        self._create_goal(title="Meta 2")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_only_own_goals(self):
        other_user = User.objects.create_user(
            email="other@example.com", password="password123"
        )
        Goal.objects.create(
            user=other_user,
            title="Other Goal",
            target_amount=Decimal("5000.00"),
        )
        self._create_goal()
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)

    def test_update_goal(self):
        goal = self._create_goal()
        goal_id = goal.data["id"]
        response = self.client.patch(
            f"{self.url}{goal_id}/",
            {"current_amount": "5000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_amount"], "5000.00")

    def test_delete_goal(self):
        goal = self._create_goal()
        goal_id = goal.data["id"]
        response = self.client.delete(f"{self.url}{goal_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Goal.objects.count(), 0)

    def test_progress_property(self):
        goal = self._create_goal(target_amount="10000.00")
        goal_id = goal.data["id"]
        self.client.patch(
            f"{self.url}{goal_id}/",
            {"current_amount": "3000.00"},
            format="json",
        )
        response = self.client.get(f"{self.url}{goal_id}/")
        self.assertEqual(response.data["progress"], 30.0)

    def test_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GoalIsolationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/goals/"
        self.user_a = User.objects.create_user(
            email="user_a@example.com", password="password123"
        )
        self.user_b = User.objects.create_user(
            email="user_b@example.com", password="password123"
        )
        self.goal_a = Goal.objects.create(
            user=self.user_a,
            title="Goal A",
            target_amount=Decimal("1000.00"),
        )
        self.goal_b = Goal.objects.create(
            user=self.user_b,
            title="Goal B",
            target_amount=Decimal("2000.00"),
        )

    def test_user_a_cannot_see_user_b_goals(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.goal_a.id)

    def test_user_b_cannot_see_user_a_goals(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.goal_b.id)

    def test_user_a_cannot_get_user_b_goal_by_id(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(f"{self.url}{self.goal_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_b_cannot_get_user_a_goal_by_id(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get(f"{self.url}{self.goal_a.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_a_cannot_delete_user_b_goal(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.delete(f"{self.url}{self.goal_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Goal.objects.filter(id=self.goal_b.id).exists())

    def test_user_b_cannot_delete_user_a_goal(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.delete(f"{self.url}{self.goal_a.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Goal.objects.filter(id=self.goal_a.id).exists())

    def test_user_a_cannot_update_user_b_goal(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.patch(
            f"{self.url}{self.goal_b.id}/",
            {"title": "Hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.goal_b.refresh_from_db()
        self.assertEqual(self.goal_b.title, "Goal B")

    def test_user_b_cannot_update_user_a_goal(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.patch(
            f"{self.url}{self.goal_a.id}/",
            {"title": "Hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.goal_a.refresh_from_db()
        self.assertEqual(self.goal_a.title, "Goal A")

    def test_create_goal_associates_to_authenticated_user(self):
        self.client.force_authenticate(user=self.user_a)
        data = {
            "title": "New Goal",
            "target_amount": "500.00",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        goal = Goal.objects.get(id=response.data["id"])
        self.assertEqual(goal.user, self.user_a)
        self.assertNotEqual(goal.user, self.user_b)
