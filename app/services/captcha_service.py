import logging

import requests

logger = logging.getLogger(__name__)

from app.config import TURNSTILE_SECRET


async def verificar_turnstile(
    token: str,
    ip: str
) -> bool:
    """
    Verifica un token de Cloudflare Turnstile.

    Devuelve:
        True  -> CAPTCHA válido
        False -> CAPTCHA inválido
    """

    try:

        response = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": TURNSTILE_SECRET,
                "response": token,
                "remoteip": ip
            },
            timeout=10
        )

        resultado = response.json()

        return resultado.get("success", False)

    except requests.RequestException:

        logger.exception(
            "Error verificando Turnstile."
        )

        return False