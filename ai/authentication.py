from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class AIAuthentication(BaseAuthentication):

    def authenticate(self, request):

        api_key = request.headers.get("X-API-Key")

        if not api_key:
            raise AuthenticationFailed("API Key não enviada.")

        if api_key != settings.AUTHENTICATION_API_KEY:
            raise AuthenticationFailed("API Key inválida.")

        # apenas valida a chave
        return (None, None)