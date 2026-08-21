from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.db import connection
from django.views.defaults import bad_request, server_error


def json_bad_request(request, exception):
    return JsonResponse(
        {"detail": "Requisicao invalida."},
        status=400,
    )


def json_server_error(request):
    return JsonResponse(
        {"detail": "Erro interno do servidor."},
        status=500,
    )


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    status_code = 200 if db_ok else 503
    return JsonResponse({"status": "ok" if db_ok else "error", "database": "ok" if db_ok else "error"}, status=status_code)


handler400 = json_bad_request
handler500 = json_server_error

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check),
    path("api/auth/", include("accounts.urls")),
    path("api/transactions/", include("transactions.urls")),
    path("api/categories/", include("categories.urls")),
    path("api/goals/", include("goals.urls")),
    path("api/gamification/", include("gamification.urls")),
    path("api/ai/", include("ai.urls")),
]
