from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Category
from .serializers import CategorySerializer
from gamification.services import (
    EVENT_CATEGORY_CREATED,
    handle_event,
)

# Create your views here.
class CategoryViewSet(viewsets.ModelViewSet):

    serializer_class = CategorySerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Category.objects.filter(
            user=self.request.user
        ).order_by("name")

    def perform_create(self, serializer):

       serializer.save(
           user=self.request.user
       )

       handle_event(
           EVENT_CATEGORY_CREATED,
           self.request.user,
           serializer.instance,
       )