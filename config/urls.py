from django.contrib import admin
from django.urls import path, include


from accounts.views import MeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/transactions/", include("transactions.urls")),
    path("api/ai/", include("ai.urls")),
    path("api/categories/", include("categories.urls")),
    path("api/goals/", include("goals.urls")),
       
]
