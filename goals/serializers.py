from rest_framework import serializers

from .models import Goal

class GoalSerializer(serializers.ModelSerializer):

    progress = serializers.ReadOnlyField()

    class Meta: 

        model = Goal 

        fields = (
            "id",
            "title",
            "description",
            "target_amount",
            "current_amount",
            "deadline",
            "status",
            "created_at",
            "updated_at",
            "progress",
        )

        read_only_fields = (
            "user",
            "created_at",
            "updated_at",
            "progress",
        )