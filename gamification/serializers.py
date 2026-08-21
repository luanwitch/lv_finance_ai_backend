from rest_framework import serializers

from .models import (
    Achievement,
    Challenge,
    UserAchievement,
    UserChallenge,
    XPTransaction,
)


class AchievementSerializer(serializers.ModelSerializer):

    category_label = serializers.CharField(
        source="get_category_display",
        read_only=True,
    )

    class Meta:

        model = Achievement

        fields = [
            "id",
            "code",
            "name",
            "description",
            "icon",
            "category",
            "category_label",
            "metric",
            "threshold",
            "xp_reward",
            "is_active",
        ]


class UserAchievementSerializer(serializers.ModelSerializer):

    achievement = AchievementSerializer(read_only=True)

    class Meta:

        model = UserAchievement

        fields = [
            "id",
            "achievement",
            "unlocked_at",
        ]


class ChallengeSerializer(serializers.ModelSerializer):

    class Meta:

        model = Challenge

        fields = [
            "id",
            "code",
            "name",
            "description",
            "icon",
            "metric",
            "target",
            "xp_reward",
            "is_active",
        ]


class UserChallengeSerializer(serializers.ModelSerializer):

    challenge = ChallengeSerializer(read_only=True)

    class Meta:

        model = UserChallenge

        fields = [
            "id",
            "challenge",
            "progress",
            "status",
            "completed_at",
            "updated_at",
        ]


class XPTransactionSerializer(serializers.ModelSerializer):

    class Meta:

        model = XPTransaction

        fields = [
            "id",
            "amount",
            "reason",
            "event_type",
            "related_object_type",
            "related_object_id",
            "created_at",
        ]
