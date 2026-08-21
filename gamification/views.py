import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Achievement,
    Challenge,
    UserAchievement,
    UserChallenge,
    XPTransaction,
)
from .rules import level_progress
from .serializers import (
    AchievementSerializer,
    ChallengeSerializer,
    XPTransactionSerializer,
)
from .services import run_periodic_checks
from .services.achievement_service import get_achievements_state, unlocked_count
from .services.challenge_service import completed_count, get_challenges_state
from .services.metrics_service import get_profile

logger = logging.getLogger(__name__)

DEFAULT_XP_HISTORY_LIMIT = 50
MAX_XP_HISTORY_LIMIT = 200


class GamificationProfileView(APIView):
    """GET /api/gamification/profile"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Reavaliação preguiçosa: detecta fechamento de mês e novos
        # desbloqueios que dependem apenas do tempo.
        run_periodic_checks(request.user)

        profile = get_profile(request.user)
        progress = level_progress(profile.total_xp)

        return Response(
            {
                "total_xp": profile.total_xp,
                "level": progress["level"],
                "level_name": progress["level_name"],
                "level_xp": progress["level_xp"],
                "xp_for_next_level": progress["xp_for_next_level"],
                "next_level_name": progress["next_level_name"],
                "progress_percent": progress["progress_percent"],
                "current_streak": profile.current_streak,
                "longest_streak": profile.longest_streak,
                "last_activity_date": profile.last_activity_date,
                "achievements_unlocked_count": unlocked_count(request.user),
                "total_achievements": Achievement.objects.filter(
                    is_active=True
                ).count(),
                "challenges_completed_count": completed_count(request.user),
                "total_challenges": Challenge.objects.filter(
                    is_active=True
                ).count(),
            }
        )


class GamificationAchievementsView(APIView):
    """GET /api/gamification/achievements"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        state = get_achievements_state(request.user)

        results = []
        unlocked_count_value = 0

        for achievement, unlocked_at in state:
            data = AchievementSerializer(achievement).data
            is_unlocked = unlocked_at is not None

            if is_unlocked:
                unlocked_count_value += 1

            data["unlocked"] = is_unlocked
            data["unlocked_at"] = unlocked_at

            results.append(data)

        return Response(
            {
                "results": results,
                "unlocked_count": unlocked_count_value,
                "total_count": len(results),
            }
        )


class GamificationChallengesView(APIView):
    """GET /api/gamification/challenges"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        state = get_challenges_state(request.user)

        results = []
        completed = 0

        for challenge, user_challenge in state:
            data = ChallengeSerializer(challenge).data

            if user_challenge is not None:
                data["progress"] = user_challenge.progress
                data["status"] = user_challenge.status
                data["completed_at"] = user_challenge.completed_at
            else:
                data["progress"] = 0
                data["status"] = "active"
                data["completed_at"] = None

            if data["status"] == "completed":
                completed += 1

            results.append(data)

        return Response(
            {
                "results": results,
                "completed_count": completed,
                "total_count": len(results),
            }
        )


class GamificationXPHistoryView(APIView):
    """GET /api/gamification/xp-history"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", DEFAULT_XP_HISTORY_LIMIT))
        except (TypeError, ValueError):
            limit = DEFAULT_XP_HISTORY_LIMIT

        limit = max(1, min(limit, MAX_XP_HISTORY_LIMIT))

        queryset = XPTransaction.objects.filter(user=request.user)

        serializer = XPTransactionSerializer(
            queryset[:limit],
            many=True,
        )

        return Response(
            {
                "count": queryset.count(),
                "results": serializer.data,
            }
        )
