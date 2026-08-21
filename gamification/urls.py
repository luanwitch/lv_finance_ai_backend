from django.urls import path

from .views import (
    GamificationAchievementsView,
    GamificationChallengesView,
    GamificationProfileView,
    GamificationXPHistoryView,
)

urlpatterns = [
    path("profile/", GamificationProfileView.as_view(), name="gamification-profile"),
    path(
        "achievements/",
        GamificationAchievementsView.as_view(),
        name="gamification-achievements",
    ),
    path(
        "challenges/",
        GamificationChallengesView.as_view(),
        name="gamification-challenges",
    ),
    path(
        "xp-history/",
        GamificationXPHistoryView.as_view(),
        name="gamification-xp-history",
    ),
]
