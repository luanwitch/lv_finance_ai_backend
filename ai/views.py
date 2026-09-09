from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from ai.authentication import AIAuthentication

from .serializers import ChatSerializer
from .services.chat_service import ChatService
from .services.orchestrator import AIOrchestrator


class AnalyzeAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        orchestrator = AIOrchestrator()

        result = orchestrator.analyze(request.user)

        return Response(result)


class ChatAPIView(APIView):

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_chat"

    def post(self, request):

        serializer = ChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]

        response = ChatService().chat(
            request.user,
            message
        )

        return Response(response)


class AIHealthView(APIView):

    authentication_classes = [AIAuthentication]
    permission_classes = []

    def get(self, request):
        return Response({
            "status": "online",
            "service": "LV Finance AI"
        })    