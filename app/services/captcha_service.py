import logging

import httpx

logger = logging.getLogger(__name__)

TURNSTILE_SECRET = "0x4AAAAAADeKap4zAyPENr_eDwCCf84T8os"


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

        async with httpx.AsyncClient() as client:

            response = await client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": TURNSTILE_SECRET,
                    "response": token,
                    "remoteip": ip
                }
            )

            resultado = response.json()

            return resultado.get("success", False)

    except httpx.HTTPError:

        logger.exception(
            "Error verificando Turnstile."
        )

        return False