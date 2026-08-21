from django.contrib import admin

from .models import (
    Achievement,
    Challenge,
    UserAchievement,
    UserChallenge,
    UserGamification,
    XPTransaction,
)


@admin.register(UserGamification)
class UserGamificationAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "total_xp",
        "current_streak",
        "longest_streak",
        "last_activity_date",
        "updated_at",
    )

    search_fields = ("user__email",)

    readonly_fields = ("created_at", "updated_at")


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "name",
        "category",
        "metric",
        "threshold",
        "xp_reward",
        "is_active",
    )

    list_filter = ("category", "is_active")

    search_fields = ("code", "name")


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):

    list_display = ("user", "achievement", "unlocked_at")

    list_filter = ("achievement__category",)

    search_fields = ("user__email", "achievement__name")


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "amount",
        "event_type",
        "reason",
        "created_at",
    )

    list_filter = ("event_type",)

    search_fields = ("user__email", "reason")

    readonly_fields = (
        "user",
        "amount",
        "reason",
        "event_type",
        "related_object_type",
        "related_object_id",
        "idempotency_key",
        "created_at",
    )


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "name",
        "metric",
        "target",
        "xp_reward",
        "is_active",
    )

    search_fields = ("code", "name")


@admin.register(UserChallenge)
class UserChallengeAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "challenge",
        "progress",
        "status",
        "completed_at",
    )

    list_filter = ("status",)

    search_fields = ("user__email", "challenge__name")
