from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserGamification


@receiver(
    post_save,
    sender=settings.AUTH_USER_MODEL,
    dispatch_uid="gamification_create_profile",
)
def create_user_gamification(sender, instance, created, **kwargs):
    """Cria o perfil de gamificação automaticamente para novos usuários."""
    if not created:
        return

    UserGamification.objects.get_or_create(user=instance)
