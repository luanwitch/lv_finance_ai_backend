from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Goal
from .serializers import GoalSerializer
from gamification.services import (
    EVENT_GOAL_COMPLETED,
    EVENT_GOAL_CREATED,
    EVENT_GOAL_UPDATED,
    handle_event,
)

# Create your views here.

class GoalViewSet(viewsets.ModelViewSet):

    serializer_class = GoalSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Goal.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):

        serializer.save(
            user=self.request.user
        )

        handle_event(
            EVENT_GOAL_CREATED,
            self.request.user,
            serializer.instance,
        )

    def perform_update(self, serializer):

        previous_status = serializer.instance.status

        serializer.save()

        if (
            serializer.instance.status == "completed"
            and previous_status != "completed"
        ):
            handle_event(
                EVENT_GOAL_COMPLETED,
                self.request.user,
                serializer.instance,
            )
        else:
            handle_event(
                EVENT_GOAL_UPDATED,
                self.request.user,
                serializer.instance,
            )