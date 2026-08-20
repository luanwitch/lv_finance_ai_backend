import logging

from rest_framework.views import exception_handler


logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return response

    logger.exception(
        "Unhandled exception in %s",
        context.get("view", "unknown"),
        exc_info=exc,
    )

    from rest_framework.response import Response
    from rest_framework import status

    return Response(
        {"detail": "Erro interno do servidor."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
