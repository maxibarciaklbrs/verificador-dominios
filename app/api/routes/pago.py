from fastapi import (
    APIRouter,
    Form,
    Request
)

from fastapi.responses import (
    RedirectResponse,
    HTMLResponse
)

from fastapi.templating import (
    Jinja2Templates
)

import logging


from app.services.pago_service import (
    crear_pago_usuario,
    procesar_webhook_pago
)

from app.services.stripe_service import (
    construir_evento
)

from app.config import (
    STRIPE_WEBHOOK_SECRET
)


from app.exceptions.pago_exceptions import (
    PagoError,
    UsuarioNoEncontradoError,
    UsuarioNoVerificadoError
)


router = APIRouter()

logger = logging.getLogger(__name__)


templates = Jinja2Templates(
    directory="templates"
)



# ==========================================================
# ERROR HTML
# ==========================================================

def error_html(
    request: Request,
    mensaje: str
):

    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "mensaje": mensaje
        },
        status_code=400
    )



# ==========================================================
# CREAR CHECKOUT STRIPE
# ==========================================================

@router.post(
    "/pagar",
    response_class=HTMLResponse
)
async def pagar(
    request: Request,
    email: str = Form(...)
):

    try:

        resultado = crear_pago_usuario(
            email
        )


        return RedirectResponse(
            url=resultado["checkout_url"],
            status_code=303
        )


    except UsuarioNoEncontradoError:

        return error_html(
            request,
            "Usuario no encontrado."
        )


    except UsuarioNoVerificadoError:

        return error_html(
            request,
            "Debes verificar el dominio antes del pago."
        )


    except PagoError:

        logger.exception(
            "Error iniciando pago"
        )

        return error_html(
            request,
            "No se pudo iniciar el pago."
        )



# ==========================================================
# WEBHOOK STRIPE
# ==========================================================

@router.post(
    "/stripe/webhook"
)
async def stripe_webhook(
    request: Request
):

    try:

        payload = await request.body()


        signature = request.headers.get(
            "stripe-signature"
        )


        evento = construir_evento(
            payload,
            signature,
            STRIPE_WEBHOOK_SECRET
        )


        resultado = procesar_webhook_pago(
            evento
        )


        return resultado


    except Exception as e:

        logger.exception(
            "Error procesando webhook Stripe"
        )


        return {
            "ok": False,
            "mensaje": str(e)
        }



# ==========================================================
# RETORNOS STRIPE
# ==========================================================

@router.get(
    "/pago/exitoso",
    response_class=HTMLResponse
)
async def pago_exitoso(
    request: Request
):

    return templates.TemplateResponse(
        "pago-exitoso.html",
        {
            "request": request
        }
    )



@router.get(
    "/pago/cancelado",
    response_class=HTMLResponse
)
async def pago_cancelado(
    request: Request
):

    return templates.TemplateResponse(
        "pago-cancelado.html",
        {
            "request": request
        }
    )