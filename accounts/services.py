import hashlib
import logging
import secrets

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import EmailVerificationToken, PasswordResetToken

logger = logging.getLogger(__name__)


def _token_hash(raw_token):
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_verification_token(user):
    user.email_verification_tokens.filter(used_at__isnull=True).delete()

    raw_token = secrets.token_urlsafe(32)

    EmailVerificationToken.objects.create(
        user=user,
        token_hash=_token_hash(raw_token),
        expires_at=timezone.now() + settings.EMAIL_VERIFICATION_TOKEN_LIFETIME,
    )

    return raw_token


def verify_verification_token(raw_token):
    if not raw_token:
        return "invalid", None

    token = (
        EmailVerificationToken.objects.select_related("user")
        .filter(token_hash=_token_hash(raw_token))
        .first()
    )

    if token is None:
        return "invalid", None

    user = token.user

    if user.is_verified:
        return "already_verified", user

    if token.is_expired:
        return "expired", user

    if token.is_used:
        return "invalid", user

    token.used_at = timezone.now()
    token.save(update_fields=("used_at",))

    user.is_verified = True
    user.save(update_fields=("is_verified",))

    return "success", user


def send_verification_email(user, raw_token):
    verify_url = "{}/verify-email?token={}".format(
        settings.FRONTEND_URL.rstrip("/"),
        raw_token,
    )

    context = {
        "user": user,
        "verify_url": verify_url,
        "link_validity_hours": settings.EMAIL_VERIFICATION_TOKEN_LIFETIME_HOURS,
    }

    subject = "Confirme seu e-mail - LV Finance AI"
    message = render_to_string("accounts/emails/verification_email.txt", context)
    html_message = render_to_string("accounts/emails/verification_email.html", context)

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )


def create_password_reset_token(user):
    user.password_reset_tokens.filter(used_at__isnull=True).delete()

    raw_token = secrets.token_urlsafe(32)

    PasswordResetToken.objects.create(
        user=user,
        token_hash=_token_hash(raw_token),
        expires_at=timezone.now() + settings.PASSWORD_RESET_TOKEN_LIFETIME,
    )

    return raw_token


def verify_password_reset_token(raw_token):
    if not raw_token:
        return "invalid", None

    token = (
        PasswordResetToken.objects.select_related("user")
        .filter(token_hash=_token_hash(raw_token))
        .first()
    )

    if token is None:
        return "invalid", None

    user = token.user

    if token.is_expired:
        return "expired", user

    if token.is_used:
        return "invalid", user

    return "success", user


def mark_password_reset_token_used(raw_token):
    token = (
        PasswordResetToken.objects.filter(token_hash=_token_hash(raw_token)).first()
    )

    if token is None or token.used_at is not None:
        return

    token.used_at = timezone.now()
    token.save(update_fields=("used_at",))


def send_password_reset_email(user, raw_token):
    reset_url = "{}/reset-password?token={}".format(
        settings.FRONTEND_URL.rstrip("/"),
        raw_token,
    )

    context = {
        "user": user,
        "reset_url": reset_url,
        "link_validity_hours": settings.PASSWORD_RESET_TOKEN_LIFETIME_HOURS,
    }

    subject = "Redefinição de senha - LV Finance AI"
    message = render_to_string("accounts/emails/password_reset_email.txt", context)
    html_message = render_to_string("accounts/emails/password_reset_email.html", context)

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )
