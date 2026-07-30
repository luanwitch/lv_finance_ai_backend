from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import GoalViewSet

router = DefaultRouter()

router.register(
    "",
    GoalViewSet,
    basename="goals",
)

urlpatterns = [
    path("", include(router.urls)),
]