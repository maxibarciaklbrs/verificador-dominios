from fastapi import APIRouter, Request
import logging

from app.services.stripe_service import (
    construir_evento
)

from app.services.pago_service import (
    procesar_webhook_pago
)

from app.exceptions.pago_exceptions import (
    PagoError
)

from app.config import (
    STRIPE_WEBHOOK_SECRET
)

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):

    payload = await request.body()

    signature = request.headers.get(
        "Stripe-Signature"
    )

    if not signature:

        return {
            "received": False,
            "error": "Falta la cabecera Stripe-Signature."
        }

    try:

        evento = construir_evento(
            payload=payload,
            signature=signature,
            webhook_secret=STRIPE_WEBHOOK_SECRET
        )

        resultado = procesar_webhook_pago(
            evento
        )

        return {
            "received": True,
            **resultado
        }

    except PagoError as e:

        logger.warning(str(e))

        return {
            "received": False,
            "error": "Error procesando el pago."
        }

    except Exception:

        logger.exception(
            "Error procesando webhook de Stripe."
        )

        return {
            "received": False,
            "error": "Error interno."
        }