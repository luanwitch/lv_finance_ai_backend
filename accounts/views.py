import logging

from django.contrib.auth import authenticate
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")

        if not email:
            return Response(
                {"detail": "O campo e-mail e obrigatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not password:
            return Response(
                {"detail": "O campo senha e obrigatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = authenticate(username=email, password=password)
        except Exception:
            logger.exception("Erro inesperado ao autenticar usuario: %s", email)
            return Response(
                {"detail": "Erro interno ao processar autenticacao."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if user is None:
            return Response(
                {"detail": "Credenciais invalidas."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"detail": "Conta desativada."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken.for_user(user)
        except Exception:
            logger.exception("Erro ao gerar token JWT para: %s", email)
            return Response(
                {"detail": "Erro ao gerar token de acesso."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)

        return Response(serializer.data)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "id": request.user.id,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.email,
            }
        )