from django.urls import path

from .views import ChatAPIView, AnalyzeAPIView 


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

]