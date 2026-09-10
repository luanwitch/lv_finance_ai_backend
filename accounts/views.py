import logging

from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .services import (
    create_password_reset_token,
    create_verification_token,
    mark_password_reset_token_used,
    send_password_reset_email,
    send_verification_email,
    verify_password_reset_token,
    verify_verification_token,
)

logger = logging.getLogger(__name__)

User = get_user_model()


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

        if not user.is_verified:
            return Response(
                {
                    "detail": "Confirme seu e-mail antes de entrar.",
                    "code": "email_not_verified",
                },
                status=status.HTTP_403_FORBIDDEN,
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
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        try:
            raw_token = create_verification_token(user)
            send_verification_email(user, raw_token)
        except Exception:
            logger.exception(
                "Falha ao gerar/enviar token de verificacao para %s", user.email
            )
            user.delete()
            return Response(
                {"detail": "Nao foi possivel enviar o e-mail de confirmacao. "
                 "Tente novamente em alguns instantes."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    VERIFY_RESPONSES = {
        "success": (
            status.HTTP_200_OK,
            "E-mail confirmado com sucesso.",
            "success",
        ),
        "already_verified": (
            status.HTTP_200_OK,
            "Este e-mail ja foi confirmado anteriormente.",
            "already_verified",
        ),
        "invalid": (
            status.HTTP_400_BAD_REQUEST,
            "Token de confirmacao invalido.",
            "invalid_token",
        ),
        "expired": (
            status.HTTP_400_BAD_REQUEST,
            "O link de confirmacao expirou. Solicite um novo e-mail.",
            "token_expired",
        ),
    }

    def post(self, request):
        token = (request.data.get("token") or "").strip()

        if not token:
            return Response(
                {
                    "detail": "O campo token e obrigatorio.",
                    "status": "invalid_token",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        outcome, _user = verify_verification_token(token)
        http_code, detail, status_code = self.VERIFY_RESPONSES[outcome]

        return Response(
            {"detail": detail, "status": status_code},
            status=http_code,
        )


class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "resend_verification"

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()

        if not email:
            return Response(
                {"detail": "O campo e-mail e obrigatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email=email).first()

        if user is not None and not user.is_verified:
            try:
                raw_token = create_verification_token(user)
                send_verification_email(user, raw_token)
            except Exception:
                logger.exception(
                    "Falha ao gerar/enviar novo token de verificacao para %s", email
                )
                return Response(
                    {"detail": "Nao foi possivel enviar o e-mail de confirmacao. "
                     "Tente novamente em alguns instantes."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(
            {
                "detail": (
                    "Se o e-mail estiver cadastrado, voce recebera um novo "
                    "link de confirmacao."
                )
            },
            status=status.HTTP_200_OK,
        )


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


class RequestPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email=email, is_active=True).first()

        if user is not None:
            try:
                raw_token = create_password_reset_token(user)
                send_password_reset_email(user, raw_token)
            except Exception:
                logger.exception(
                    "Falha ao gerar/enviar token de redefinicao de senha para %s", email
                )
                return Response(
                    {"detail": "Nao foi possivel enviar o e-mail de redefinicao "
                     "de senha. Tente novamente em alguns instantes."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(
            {
                "detail": (
                    "Se o e-mail estiver cadastrado, voce recebera um link "
                    "para redefinir sua senha."
                )
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    RESET_RESPONSES = {
        "success": (
            status.HTTP_200_OK,
            "Senha redefinida com sucesso. Faca login com a nova senha.",
            "success",
        ),
        "invalid": (
            status.HTTP_400_BAD_REQUEST,
            "Token de redefinicao invalido.",
            "invalid_token",
        ),
        "expired": (
            status.HTTP_400_BAD_REQUEST,
            "O link de redefinicao expirou. Solicite um novo e-mail.",
            "token_expired",
        ),
    }

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["password"]

        outcome, user = verify_password_reset_token(token)
        http_code, detail, status_code = self.RESET_RESPONSES[outcome]

        if outcome == "success":
            if user is None:
                http_code, detail, status_code = self.RESET_RESPONSES["invalid"]
            else:
                user.set_password(new_password)
                user.save(update_fields=("password",))
                mark_password_reset_token_used(token)
                user.password_reset_tokens.filter(used_at__isnull=True).delete()

        return Response(
            {"detail": detail, "status": status_code},
            status=http_code,
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            user=request.user,
        )
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=("password",))

        return Response(
            {"detail": "Senha alterada com sucesso."},
            status=status.HTTP_200_OK,
        )
