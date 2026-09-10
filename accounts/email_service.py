import logging

import httpx
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

EMAIL_API_URL = "https://api.resend.com/emails"
EMAIL_API_TIMEOUT_SECONDS = 30


class EmailSendError(Exception):
    """Falha ao transmitir o e-mail pelo provedor de API HTTP."""


def send_email(subject, message, html_message, recipient_list, from_email=None):
    api_key = (getattr(settings, "RESEND_API_KEY", "") or "").strip()

    if not api_key:
        # Ambiente local/testes: usa o backend Django configurado
        # (console, SMTP ou locmem durante a suite de testes).
        send_mail(
            subject,
            message,
            from_email or settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        return

    _send_via_http(
        api_key=api_key,
        subject=subject,
        text=message,
        html=html_message,
        to=recipient_list,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
    )


def _send_via_http(api_key, subject, text, html, to, from_email):
    payload = {
        "from": from_email,
        "to": to if isinstance(to, (list, tuple)) else [to],
        "subject": subject,
        "text": text,
        "html": html,
    }

    try:
        response = httpx.post(
            EMAIL_API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=EMAIL_API_TIMEOUT_SECONDS,
        )
    except (httpx.HTTPError, OSError) as exc:
        logger.exception("Falha na chamada HTTP ao provedor de e-mail")
        raise EmailSendError("Provedor de e-mail indisponivel") from exc

    if response.status_code >= 400:
        logger.warning(
            "Provedor de e-mail rejeitou o envio (status %s)",
            response.status_code,
        )
        raise EmailSendError("Provedor de e-mail rejeitou o envio")