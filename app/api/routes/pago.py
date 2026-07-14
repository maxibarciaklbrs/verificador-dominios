from fastapi import APIRouter, Form, Request

from fastapi.responses import RedirectResponse, HTMLResponse

from fastapi.templating import Jinja2Templates

import logging


from app.services.pago_service import crear_pago_usuario, procesar_webhook_pago

from app.services.stripe_service import construir_evento

from app.config import STRIPE_WEBHOOK_SECRET


from app.exceptions.pago_exceptions import (
    PagoError,
    UsuarioNoEncontradoError,
    UsuarioNoVerificadoError,
)

from app.services.stripe_service import construir_evento, obtener_checkout_session

from app.database.usuarios import obtener_usuario_por_id

from app.database.dominios import obtener_dominio_por_id

router = APIRouter()

logger = logging.getLogger(__name__)


templates = Jinja2Templates(directory="templates")


# ==========================================================
# ERROR HTML
# ==========================================================


def error_html(msg: str):
    return f"""
    <html>
        <head>
            <link rel="stylesheet" href="/static/css/style.css">
        </head>

        <body style="
            text-align:center;
            background-image: url('/static/assets/images/oficinas_klbrs.png');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            min-height: 100vh;
        ">

            <div style="
                background: white;
                padding: 3em;
                max-width: 600px;
                margin: 5em auto;
                border-radius: 10px;
                text-align: center;
            ">

                <h1>{msg}</h1>

                <a class="button" href="/">
                    ← Volver al inicio
                </a>

            </div>

        </body>

    </html>
    """


# ==========================================================
# CREAR CHECKOUT STRIPE
# ==========================================================


@router.post("/pagar", response_class=HTMLResponse)
async def pagar(request: Request, email: str = Form(...)):

    try:

        resultado = crear_pago_usuario(email)

        return RedirectResponse(url=resultado["checkout_url"], status_code=303)

    except UsuarioNoEncontradoError:

        return error_html(request, "Usuario no encontrado.")

    except UsuarioNoVerificadoError:

        return error_html(request, "Debes verificar el dominio antes del pago.")

    except PagoError:

        logger.exception("Error iniciando pago")

        return error_html(request, "No se pudo iniciar el pago.")


# ==========================================================
# WEBHOOK STRIPE
# ==========================================================


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):

    try:

        payload = await request.body()

        signature = request.headers.get("stripe-signature")

        evento = construir_evento(payload, signature, STRIPE_WEBHOOK_SECRET)

        resultado = procesar_webhook_pago(evento)

        return resultado

    except Exception as e:

        logger.exception("Error procesando webhook Stripe")

        return {"ok": False, "mensaje": str(e)}


# ==========================================================
# RETORNOS STRIPE
# ==========================================================


@router.get("/pago/exitoso")
async def pago_exitoso(request: Request, session_id: str):

    session = obtener_checkout_session(session_id)

    usuario_id = int(session.metadata["usuario_id"])

    usuario = obtener_usuario_por_id(usuario_id)

    dominio = obtener_dominio_por_id(usuario["dominio_id"])

    return templates.TemplateResponse(
        "registro-confirmacion.html",
        {
            "request": request,
            "nombre": usuario["nombre"],
            "apellido": usuario["apellido"],
            "email": usuario["email"],
            "telefono": usuario["telefono"],
            "codigo": dominio["codigo"],
            "dominio": dominio["nombre"],
            "ya_existia": True,
            "verificado": True,
            "pagado": True,
        },
    )


@router.get("/pago/cancelado")
async def pago_cancelado(request: Request, session_id: str):

    session = obtener_checkout_session(session_id)

    usuario_id = int(session.metadata["usuario_id"])

    usuario = obtener_usuario_por_id(usuario_id)

    dominio = obtener_dominio_por_id(usuario["dominio_id"])

    return templates.TemplateResponse(
        "registro-confirmacion.html",
        {
            "request": request,
            "nombre": usuario["nombre"],
            "apellido": usuario["apellido"],
            "email": usuario["email"],
            "telefono": usuario["telefono"],
            "codigo": dominio["codigo"],
            "dominio": dominio["nombre"],
            "ya_existia": True,
            "verificado": True,
            "pagado": False,
        },
    )
