from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from categories.models import Category
from goals.models import Goal
from transactions.models import Transaction

from .models import (
    UserAchievement,
    UserGamification,
    XPTransaction,
)
from .services import handle_event
from .services.achievement_service import sync_definitions
from .services.xp_service import award_xp, get_profile

User = get_user_model()


class GamificationTestBase(TestCase):

    def setUp(self):
        super().setUp()

        # O cache de sincronização é por processo; os dados de teste
        # são revertidos a cada teste, então força ressincronização.
        sync_definitions(force=True)

        self.client = APIClient()

        self.user = User.objects.create_user(
            email="gamer@example.com",
            password="strongpassword123",
        )

        self.client.force_authenticate(user=self.user)


class GamificationProfileTests(GamificationTestBase):

    def test_profile_auto_created_on_user_creation(self):
        self.assertTrue(
            UserGamification.objects.filter(user=self.user).exists()
        )

    def test_get_profile_creates_if_missing(self):
        UserGamification.objects.all().delete()

        response = self.client.get("/api/gamification/profile/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            UserGamification.objects.filter(user=self.user).exists()
        )
        self.assertEqual(response.data["total_xp"], 0)
        self.assertEqual(response.data["level"], 1)

    def test_profile_response_shape(self):
        response = self.client.get("/api/gamification/profile/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_keys = {
            "total_xp",
            "level",
            "level_name",
            "level_xp",
            "xp_for_next_level",
            "next_level_name",
            "progress_percent",
            "current_streak",
            "longest_streak",
            "last_activity_date",
            "achievements_unlocked_count",
            "total_achievements",
            "challenges_completed_count",
            "total_challenges",
        }
        self.assertTrue(expected_keys.issubset(set(response.data.keys())))


class GamificationPermissionTests(GamificationTestBase):

    def test_all_endpoints_require_authentication(self):
        self.client.force_authenticate(user=None)

        urls = [
            "/api/gamification/profile/",
            "/api/gamification/achievements/",
            "/api/gamification/challenges/",
            "/api/gamification/xp-history/",
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                url,
            )


class XPAwardTests(GamificationTestBase):

    def _create_transaction(self, **overrides):
        data = {
            "title": "Almoço",
            "amount": "45.90",
            "category": "alimentacao",
            "type": "expense",
            "date": str(timezone.now().date()),
            "description": "",
        }
        data.update(overrides)
        return self.client.post(
            "/api/transactions/transactions/", data, format="json"
        )

    def test_first_transaction_awards_bonus_instead_of_regular_xp(self):
        response = self._create_transaction()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        profile = get_profile(self.user)
        # +50 primeira transação e +25 conquista "primeira transação"
        self.assertEqual(profile.total_xp, 75)
        self.assertTrue(
            XPTransaction.objects.filter(
                user=self.user, event_type="first_transaction"
            ).exists()
        )
        self.assertFalse(
            XPTransaction.objects.filter(
                user=self.user, event_type="transaction_created"
            ).exists()
        )

    def test_subsequent_transactions_award_regular_xp(self):
        self._create_transaction(title="T1")
        self._create_transaction(title="T2")
        self._create_transaction(title="T3")

        profile = get_profile(self.user)
        # 50 + 25 (conquista) + 5 + 5
        self.assertEqual(profile.total_xp, 85)

    def test_deleted_transactions_do_not_allow_refarm_first_bonus(self):
        self._create_transaction(title="T1")
        Transaction.objects.all().delete()

        self._create_transaction(title="T1 novamente")

        profile = get_profile(self.user)
        # Nada além dos 75 originais: bônus de primeira transação é
        # único (idempotência por chave) e o ramo "count == 1" não
        # concede o XP regular.
        self.assertEqual(profile.total_xp, 75)

    def test_duplicate_event_does_not_double_award(self):
        # Duas transações: a primeira passa pelo pipeline (como na
        # produção, via hook da view) e a segunda segue o fluxo de XP
        # regular.
        first = Transaction.objects.create(
            user=self.user,
            title="Tx 1",
            amount=Decimal("10.00"),
            type="expense",
            date=timezone.now().date(),
        )
        handle_event("transaction_created", self.user, first)

        second = Transaction.objects.create(
            user=self.user,
            title="Tx 2",
            amount=Decimal("10.00"),
            type="expense",
            date=timezone.now().date(),
        )

        handle_event("transaction_created", self.user, second)
        handle_event("transaction_created", self.user, second)
        handle_event("transaction_created", self.user, second)

        profile = get_profile(self.user)
        # +50 primeira transação, +25 conquista e apenas UM +5.
        self.assertEqual(profile.total_xp, 80)
        self.assertEqual(
            XPTransaction.objects.filter(
                user=self.user, event_type="transaction_created"
            ).count(),
            1,
        )

    def test_category_creation_awards_xp_once(self):
        payload = {
            "name": "Saúde",
            "icon": "💊",
            "type": "expense",
        }

        response = self.client.post("/api/categories/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        profile = get_profile(self.user)
        # +10 categoria e +25 conquista primeira categoria
        self.assertEqual(profile.total_xp, 35)

        Category.objects.filter(user=self.user).delete()

        response = self.client.post("/api/categories/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        profile.refresh_from_db()
        # Conquista já desbloqueada; XP da segunda categoria também
        # é concedido (+10).
        self.assertEqual(profile.total_xp, 45)

    def test_goal_lifecycle_xp(self):
        create_response = self.client.post(
            "/api/goals/",
            {
                "title": "Reserva de emergência",
                "target_amount": "10000.00",
                "current_amount": "0.00",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        goal_id = create_response.data["id"]

        profile = get_profile(self.user)
        # +30 meta criada, +25 conquista primeira meta, +25 conquista
        # "criou uma meta" e +50 desafio "Meta".
        self.assertEqual(profile.total_xp, 130)

        update_url = f"/api/goals/{goal_id}/"

        self.client.patch(update_url, {"description": "x"}, format="json")
        profile.refresh_from_db()
        self.assertEqual(profile.total_xp, 135)

        # Segunda atualização no mesmo dia: cooldown anti-abuso.
        self.client.patch(update_url, {"description": "y"}, format="json")
        profile.refresh_from_db()
        self.assertEqual(profile.total_xp, 135)

        self.client.patch(
            update_url, {"status": "completed"}, format="json"
        )
        profile.refresh_from_db()
        # +100 conclusão e +50 conquista "concluiu uma meta"
        self.assertEqual(profile.total_xp, 285)

        self.assertEqual(
            XPTransaction.objects.filter(
                user=self.user, event_type="goal_created"
            ).count(),
            1,
        )
        self.assertEqual(
            XPTransaction.objects.filter(
                user=self.user, event_type="goal_updated"
            ).count(),
            1,
        )
        self.assertEqual(
            XPTransaction.objects.filter(
                user=self.user, event_type="goal_completed"
            ).count(),
            1,
        )

    def test_gamification_failure_does_not_break_transaction_flow(self):
        with mock.patch(
            "gamification.services.gamification_service.evaluate_achievements",
            side_effect=Exception("boom"),
        ):
            response = self._create_transaction()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)


class LevelProgressionTests(GamificationTestBase):

    def _profile_payload(self):
        return self.client.get("/api/gamification/profile/").data

    def _award(self, amount, key_suffix):
        award_xp(
            self.user,
            amount=amount,
            reason="teste",
            event_type="test_event",
            idempotency_key=f"test:{key_suffix}",
        )

    def test_initial_level(self):
        data = self._profile_payload()

        self.assertEqual(data["level"], 1)
        self.assertEqual(data["level_name"], "Iniciante")
        self.assertEqual(data["progress_percent"], 0)
        self.assertEqual(data["xp_for_next_level"], 100)

    def test_level_up_crossing_threshold(self):
        self._award(95, "a")
        data = self._profile_payload()
        self.assertEqual(data["level"], 1)

        self._award(10, "b")  # 105 XP
        data = self._profile_payload()
        self.assertEqual(data["level"], 2)
        self.assertEqual(data["level_name"], "Organizado")
        self.assertEqual(data["level_xp"], 5)
        self.assertEqual(data["xp_for_next_level"], 195)
        self.assertEqual(data["progress_percent"], 2)

    def test_mid_levels_progress_math(self):
        self._award(350, "a")
        data = self._profile_payload()

        self.assertEqual(data["level"], 3)
        self.assertEqual(data["level_name"], "Controlador")
        self.assertEqual(data["level_xp"], 50)
        self.assertEqual(data["progress_percent"], 16)

    def test_max_level_caps_progress(self):
        self._award(99999, "a")
        data = self._profile_payload()

        self.assertEqual(data["level"], 7)
        self.assertEqual(data["level_name"], "Mestre Financeiro")
        self.assertIsNone(data["xp_for_next_level"])
        self.assertEqual(data["progress_percent"], 100)


class AchievementTests(GamificationTestBase):

    def test_first_transaction_unlocks_achievement(self):
        Transaction.objects.create(
            user=self.user,
            title="Tx",
            amount=Decimal("10.00"),
            type="expense",
            date=timezone.now().date(),
        )
        handle_event("transaction_created", self.user, None)

        unlocked = UserAchievement.objects.filter(user=self.user)
        self.assertEqual(unlocked.count(), 1)
        self.assertEqual(unlocked.first().achievement.code, "first_transaction")
        self.assertIsNotNone(unlocked.first().unlocked_at)

    def test_no_duplicate_user_achievement_rows(self):
        for index in range(12):
            Transaction.objects.create(
                user=self.user,
                title=f"Tx {index}",
                amount=Decimal("10.00"),
                type="expense",
                date=timezone.now().date(),
            )

        # Avaliações repetidas (simulando chamadas concorrentes/lazy)
        from .services.gamification_service import run_periodic_checks

        run_periodic_checks(self.user)
        run_periodic_checks(self.user)

        # 12 transações desbloqueiam first_transaction (limiar 1) e
        # transactions_10 (limiar 10): duas linhas, cada uma única.
        self.assertEqual(
            UserAchievement.objects.filter(user=self.user).count(), 2
        )
        self.assertEqual(
            UserAchievement.objects.filter(
                user=self.user, achievement__code="transactions_10"
            ).count(),
            1,
        )
        self.assertEqual(
            UserAchievement.objects.filter(
                user=self.user, achievement__code="first_transaction"
            ).count(),
            1,
        )

    def test_achievement_xp_granted_once(self):
        for index in range(12):
            Transaction.objects.create(
                user=self.user,
                title=f"Tx {index}",
                amount=Decimal("10.00"),
                type="expense",
                date=timezone.now().date(),
            )

        from .services.gamification_service import run_periodic_checks

        run_periodic_checks(self.user)
        profile = get_profile(self.user)
        total_after_first = profile.total_xp

        run_periodic_checks(self.user)
        profile.refresh_from_db()

        self.assertEqual(profile.total_xp, total_after_first)

    def test_achievements_endpoint_flags(self):
        Category.objects.create(
            user=self.user,
            name="Mercado",
            icon="🛒",
            type="expense",
        )
        handle_event("category_created", self.user, None)

        response = self.client.get("/api/gamification/achievements/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        by_code = {item["code"]: item for item in results}

        self.assertTrue(by_code["first_category"]["unlocked"])
        self.assertIsNotNone(by_code["first_category"]["unlocked_at"])
        self.assertFalse(by_code["transactions_100"]["unlocked"])
        self.assertIsNone(by_code["transactions_100"]["unlocked_at"])
        self.assertEqual(response.data["unlocked_count"], 1)


class StreakTests(GamificationTestBase):

    def _transact(self):
        Transaction.objects.create(
            user=self.user,
            title="Tx",
            amount=Decimal("10.00"),
            type="expense",
            date=timezone.now().date(),
        )

    def _set_last_activity_days_ago(
        self, days, current_streak=None, longest_streak=None
    ):
        profile = get_profile(self.user)
        profile.last_activity_date = timezone.localdate() - timedelta(days=days)
        if current_streak is not None:
            profile.current_streak = current_streak
        if longest_streak is not None:
            profile.longest_streak = longest_streak
        profile.save()
        return profile

    def test_multiple_actions_same_day_count_as_one(self):
        handle_event("transaction_created", self.user, None)
        handle_event("transaction_created", self.user, None)
        handle_event("category_created", self.user, None)

        profile = get_profile(self.user)
        self.assertEqual(profile.current_streak, 1)
        self.assertEqual(profile.longest_streak, 1)

    def test_consecutive_day_increments_streak(self):
        self._set_last_activity_days_ago(1, current_streak=3)

        handle_event("transaction_created", self.user, None)

        profile = get_profile(self.user)
        self.assertEqual(profile.current_streak, 4)
        self.assertEqual(profile.longest_streak, 4)

    def test_gap_resets_streak_to_one(self):
        self._set_last_activity_days_ago(
            3, current_streak=9, longest_streak=9
        )

        handle_event("transaction_created", self.user, None)

        profile = get_profile(self.user)
        self.assertEqual(profile.current_streak, 1)
        self.assertEqual(profile.longest_streak, 9)

    def test_milestone_bonus_awarded_once(self):
        self._set_last_activity_days_ago(1, current_streak=6)

        handle_event("transaction_created", self.user, None)

        bonuses = XPTransaction.objects.filter(
            user=self.user, event_type="streak_bonus"
        )
        self.assertEqual(bonuses.count(), 1)
        self.assertEqual(bonuses.first().amount, 20)

        profile = get_profile(self.user)
        self.assertEqual(profile.current_streak, 7)

        # Mesmo dia, nova ação: nenhum bônus adicional.
        handle_event("category_created", self.user, None)
        self.assertEqual(
            XPTransaction.objects.filter(
                user=self.user, event_type="streak_bonus"
            ).count(),
            1,
        )

    def test_milestone_not_reawarded_after_cycle(self):
        self._set_last_activity_days_ago(1, current_streak=6)
        handle_event("transaction_created", self.user, None)

        self._set_last_activity_days_ago(1, current_streak=6)
        handle_event("transaction_created", self.user, None)

        self.assertEqual(
            XPTransaction.objects.filter(
                user=self.user, event_type="streak_bonus"
            ).count(),
            1,
        )


class MonthCloseTests(GamificationTestBase):

    def _previous_month_day(self, day=15):
        today = timezone.localdate()
        if today.month == 1:
            return today.replace(year=today.year - 1, month=12, day=day)
        return today.replace(month=today.month - 1, day=day)

    def test_previous_complete_month_awards_xp_and_achievements(self):
        month_day = self._previous_month_day()

        Transaction.objects.create(
            user=self.user,
            title="Salário",
            amount=Decimal("5000.00"),
            type="income",
            date=month_day,
        )
        Transaction.objects.create(
            user=self.user,
            title="Mercado",
            amount=Decimal("200.00"),
            type="expense",
            date=month_day,
        )

        response = self.client.get("/api/gamification/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # +100 mês fechado com controle financeiro
        self.assertTrue(
            XPTransaction.objects.filter(
                user=self.user, event_type="month_closed"
            ).exists()
        )

        codes = set(
            UserAchievement.objects.filter(user=self.user).values_list(
                "achievement__code", flat=True
            )
        )
        self.assertIn("first_month_complete", codes)
        self.assertIn("first_month_within_budget", codes)
        self.assertNotIn("three_months_within_budget", codes)

        profile = get_profile(self.user)
        # 100 mês fechado + 50 first_month_complete + 75
        # first_month_within_budget + 25 first_transaction (as duas
        # transações criadas desbloqueiam a conquista de primeira
        # transação).
        self.assertEqual(profile.total_xp, 250)

    def test_month_close_xp_awarded_only_once(self):
        month_day = self._previous_month_day()

        Transaction.objects.create(
            user=self.user,
            title="Salário",
            amount=Decimal("5000.00"),
            type="income",
            date=month_day,
        )
        Transaction.objects.create(
            user=self.user,
            title="Mercado",
            amount=Decimal("200.00"),
            type="expense",
            date=month_day,
        )

        from .services.gamification_service import run_periodic_checks

        run_periodic_checks(self.user)
        run_periodic_checks(self.user)

        self.assertEqual(
            XPTransaction.objects.filter(
                user=self.user, event_type="month_closed"
            ).count(),
            1,
        )


class ChallengeTests(GamificationTestBase):

    def test_starting_challenge_completes_with_five_uncategorized_transactions(self):
        for index in range(5):
            Transaction.objects.create(
                user=self.user,
                title=f"Tx {index}",
                amount=Decimal("10.00"),
                category="",
                type="expense",
                date=timezone.now().date(),
            )
            handle_event("transaction_created", self.user, None)

        from .models import UserChallenge

        state = UserChallenge.objects.get(
            user=self.user, challenge__code="challenge_starting"
        )
        self.assertEqual(state.progress, 5)
        self.assertEqual(state.status, "completed")
        self.assertIsNotNone(state.completed_at)

        self.assertEqual(
            XPTransaction.objects.filter(
                user=self.user, event_type="challenge_completed"
            ).count(),
            1,
        )

    def test_challenge_completion_awards_xp_once(self):
        for index in range(5):
            Transaction.objects.create(
                user=self.user,
                title=f"Tx {index}",
                amount=Decimal("10.00"),
                category="",
                type="expense",
                date=timezone.now().date(),
            )
            handle_event("transaction_created", self.user, None)

        from .services.gamification_service import run_periodic_checks

        run_periodic_checks(self.user)
        profile = get_profile(self.user)
        total_before = profile.total_xp

        run_periodic_checks(self.user)
        profile.refresh_from_db()

        self.assertEqual(profile.total_xp, total_before)

    def test_organization_challenge_requires_min_categorized_transactions(self):
        for index in range(3):
            Transaction.objects.create(
                user=self.user,
                title=f"Categorizada {index}",
                amount=Decimal("10.00"),
                category="outros",
                type="expense",
                date=timezone.now().date(),
            )
            handle_event("transaction_created", self.user, None)

        from .models import UserChallenge

        state = UserChallenge.objects.get(
            user=self.user, challenge__code="challenge_organization"
        )
        self.assertEqual(state.status, "active")

    def test_challenges_endpoint_shape(self):
        Transaction.objects.create(
            user=self.user,
            title="Tx",
            amount=Decimal("10.00"),
            type="expense",
            date=timezone.now().date(),
        )
        handle_event("transaction_created", self.user, None)

        response = self.client.get("/api/gamification/challenges/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        self.assertTrue(len(results) >= 4)

        starting = next(
            item
            for item in results
            if item["code"] == "challenge_starting"
        )
        self.assertEqual(starting["progress"], 1)
        self.assertEqual(starting["status"], "active")
        self.assertEqual(starting["xp_reward"], 50)
        self.assertIsNone(starting["completed_at"])

    def test_consistency_challenge_tracks_longest_streak(self):
        profile = get_profile(self.user)
        profile.longest_streak = 9
        profile.save()

        from .services.gamification_service import run_periodic_checks

        run_periodic_checks(self.user)

        from .models import UserChallenge

        state = UserChallenge.objects.get(
            user=self.user, challenge__code="challenge_consistency"
        )
        self.assertEqual(state.progress, 7)
        self.assertEqual(state.status, "completed")


class DataIsolationTests(GamificationTestBase):

    def setUp(self):
        super().setUp()

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="strongpassword123",
        )

        Transaction.objects.create(
            user=self.user,
            title="Minha transação",
            amount=Decimal("10.00"),
            type="expense",
            date=timezone.now().date(),
        )
        handle_event("transaction_created", self.user, None)

    def test_profile_shows_only_own_data(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get("/api/gamification/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_xp"], 0)
        self.assertEqual(response.data["achievements_unlocked_count"], 0)

    def test_xp_history_shows_only_own_entries(self):
        response = self.client.get("/api/gamification/xp-history/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get("/api/gamification/xp-history/")
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_achievements_isolated_between_users(self):
        response = self.client.get("/api/gamification/achievements/")
        self.assertEqual(response.data["unlocked_count"], 1)

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get("/api/gamification/achievements/")
        self.assertEqual(response.data["unlocked_count"], 0)

    def test_challenges_isolated_between_users(self):
        response = self.client.get("/api/gamification/challenges/")
        starting = next(
            item
            for item in response.data["results"]
            if item["code"] == "challenge_starting"
        )
        self.assertEqual(starting["progress"], 1)

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get("/api/gamification/challenges/")
        starting = next(
            item
            for item in response.data["results"]
            if item["code"] == "challenge_starting"
        )
        self.assertEqual(starting["progress"], 0)


class XPHistoryEndpointTests(GamificationTestBase):

    def test_limit_parameter(self):
        for index in range(5):
            award_xp(
                self.user,
                amount=5,
                reason=f"r{index}",
                event_type="test_event",
                idempotency_key=f"k{index}",
            )

        response = self.client.get("/api/gamification/xp-history/?limit=3")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)
        self.assertEqual(len(response.data["results"]), 3)

        entry_keys = {entry["event_type"] for entry in response.data["results"]}
        self.assertIn("test_event", entry_keys)

    def test_invalid_limit_falls_back_to_default(self):
        response = self.client.get("/api/gamification/xp-history/?limit=abc")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
