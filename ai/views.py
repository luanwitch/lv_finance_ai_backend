from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .services.orchestrator import AIOrchestrator
from .services.chat_service import ChatService

# Create your views here.
class AnalyzeAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        orchestrator = AIOrchestrator()

        result = orchestrator.analyze(request.user)

        return Response(result)

class ChatAPIView(APIView):

        permission_classes = [IsAuthenticated]

        def post(self, request):

            message = request.data.get("message", "")

            response = ChatService().chat(
                request.user,
                message
            )

            return Response(response)

           