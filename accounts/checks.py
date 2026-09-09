import os
import sys

from django.core.checks import Warning, register

LOCAL_DB_HOSTS = {"localhost", "127.0.0.1", "::1"}


@register("accounts.W001")
def warn_if_remote_db_in_debug(app_configs=None, **kwargs):
    """Avisa quando o servidor roda com DEBUG=True apontando para um banco remoto.

    Cenario real: `manage.py runserver` com DATABASE_URL apontando para o
    Neon (producao) enquanto o operador acha que esta mexendo no dev.sqlite3.
    """
    if "test" in sys.argv:
        return []

    debug = os.getenv("DJANGO_DEBUG", "False").lower() == "true"
    database_url = os.getenv("DATABASE_URL", "")

    if not debug or not database_url:
        return []

    lowered = database_url.lower()

    if lowered.startswith(("sqlite:", "spatialite:")):
        return []

    host = lowered.split("://", 1)[-1].split("/")[0].split("@")[-1]
    hostname = host.split(":")[0]

    if hostname in LOCAL_DB_HOSTS:
        return []

    return [
        Warning(
            f"DATABASE_URL aponta para um banco remoto ('{hostname}') com "
            "DJANGO_DEBUG=True. Operacoes locais podem alterar o banco de "
            "producao por engano (verificacao da auditoria P0).",
            hint=(
                "Use start_dev.ps1 (forca sqlite:///dev.sqlite3) para "
                "desenvolvimento/validacao local, ou defina DJANGO_DEBUG=False "
                "se o acesso remoto for intencional."
            ),
            id="accounts.W001",
        )
    ]