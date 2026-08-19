from django.urls import path

from .views import AIHealthView, ChatAPIView, AnalyzeAPIView 


urlpatterns = [

    path(
        "analyze/",
         AnalyzeAPIView.as_view(),
        name="ai-analysis"
    ),

    path(
        "chat/",
        ChatAPIView.as_view()
    ),

    path("health/", AIHealthView.as_view()),

]