from rest_framework import serializers

from .models import Goal

class GoalSerializer(serializers.ModelSerializer):

    progress = serializers.ReadOnlyField()

    class Meta: 

        model = Goal 

        fields = "__all__"

        read_only_fields = (
            "user",
            "created_at",
            "updated_at",
            "progress",
        )