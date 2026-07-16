<<<<<<< HEAD
=======
from fastapi import APIRouter, Form, Request

from fastapi.responses import RedirectResponse, HTMLResponse

from fastapi.templating import Jinja2Templates

>>>>>>> dev
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from app.services.dns_service import obtener_usuario_por_codigo, marcar_pagado
from app.services.telegram_service import enviar_notificacion_pago_telegram
import stripe
import os
from dotenv import load_dotenv

<<<<<<< HEAD
load_dotenv()
=======

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

>>>>>>> dev
logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Configurar Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# ============================================
# ENDPOINT LEGACY (SIMULACIÓN MANUAL)
# ============================================

<<<<<<< HEAD
@router.post("/webhook-pago")
async def webhook_pago(request: Request):
    """
    ENDPOINT EXISTENTE - Se mantiene para compatibilidad
    (Simulación de pago manual)
    """
    try:
        data = await request.json()
        codigo = data.get("codigo")
        monto = data.get("monto", 50.00)
        
        # Buscar usuario por código
        usuario = obtener_usuario_por_codigo(codigo)
        
        if not usuario:
            return {"exitoso": False, "mensaje": "Código no encontrado"}
        
        if usuario.get("pagado", False):
            return {"exitoso": True, "mensaje": "Este pago ya había sido confirmado anteriormente"}
        
        email = usuario.get("email")
        
        # Marcar como pagado en SQLite
        marcar_pagado(email)
        
        # Registrar en archivo de pagos
        with open("pagos_registrados.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | {email} | {usuario.get('nombre', '')} | {usuario.get('apellido', '')} | CODIGO: {codigo} | MONTO: ${monto} | MANUAL\n")
        
        logger.info(f"Pago registrado manualmente: {email} - ${monto}")
        
        # Notificación Telegram
        try:
            enviar_notificacion_pago_telegram(usuario, codigo, monto)
        except Exception as e:
            logger.error(f"Error enviando Telegram: {e}")
        
        return {
            "exitoso": True,
            "mensaje": f"Pago confirmado correctamente. Monto: ${monto}."
        }
    except Exception as e:
        logger.error(f"Error en webhook-pago: {e}")
        return {"exitoso": False, "mensaje": str(e)}

# ============================================
# ENDPOINTS DE STRIPE
# ============================================

@router.post("/crear-sesion-stripe")
async def crear_sesion_stripe(request: Request):
    """
    Crea una sesión de pago en Stripe
    """
    try:
        data = await request.json()
        codigo = data.get("codigo")
        email = data.get("email")
        
        if not codigo or not email:
            return JSONResponse(
                status_code=400,
                content={"exitoso": False, "mensaje": "Faltan datos: codigo y email"}
            )
        
        # Verificar que el código existe
        usuario = obtener_usuario_por_codigo(codigo)
        if not usuario:
            return JSONResponse(
                status_code=404,
                content={"exitoso": False, "mensaje": "Código no encontrado"}
            )
        
        # Verificar que no esté ya pagado
        if usuario.get("pagado", False):
            return JSONResponse(
                status_code=400,
                content={"exitoso": False, "mensaje": "Este código ya ha pagado"}
            )
        
        # Crear sesión en Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "Escaneo de Vulnerabilidades",
                        "description": f"Verificación y escaneo para: {email}",
                    },
                    "unit_amount": 5000,  # 50.00 EUR
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="http://localhost:8000/api/pago/pago-exitoso?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:8000/api/pago/pago-cancelado",
            customer_email=email,
            metadata={
                "codigo": codigo,
                "email": email,
                "monto": "50.00"
            }
        )
        
        return {
            "exitoso": True,
            "checkout_url": session.url,
            "session_id": session.id
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Error Stripe: {e}")
        return JSONResponse(
            status_code=400,
            content={"exitoso": False, "mensaje": f"Error de Stripe: {str(e)}"}
        )
    except Exception as e:
        logger.error(f"Error creando sesión: {e}")
        return JSONResponse(
            status_code=500,
            content={"exitoso": False, "mensaje": f"Error interno: {str(e)}"}
        )

@router.post("/webhook-stripe")
async def webhook_stripe(request: Request):
    """
    Webhook de Stripe - Recibe la confirmación de pago
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if not webhook_secret:
            logger.error("STRIPE_WEBHOOK_SECRET no configurado")
            return JSONResponse(
                status_code=500,
                content={"error": "Webhook secret no configurado"}
            )
        
        # Verificar firma
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except stripe.error.SignatureVerificationError:
            logger.error("Firma inválida")
            return JSONResponse(
                status_code=400,
                content={"error": "Firma inválida"}
            )
        
        # Procesar evento de pago completado
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            
            # Extraer datos de metadata
            codigo = session.get("metadata", {}).get("codigo")
            email = session.get("metadata", {}).get("email")
            monto = session.get("metadata", {}).get("monto", 50.00)
            
            logger.info(f"✅ Pago confirmado por Stripe: {email} - Código: {codigo}")
            
            # Verificar que el usuario existe
            usuario = obtener_usuario_por_codigo(codigo)
            if not usuario:
                logger.error(f"Código no encontrado: {codigo}")
                return {"error": "Código no encontrado"}, 404
            
            # Verificar que no esté ya pagado
            if usuario.get("pagado", False):
                logger.info(f"Pago ya confirmado para: {email}")
                return {"mensaje": "Pago ya confirmado"}, 200
            
            # Marcar como pagado en SQLite
            marcar_pagado(email)
            
            # Registrar en archivo de pagos
            with open("pagos_registrados.txt", "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} | {email} | {usuario.get('nombre', '')} | {usuario.get('apellido', '')} | CODIGO: {codigo} | MONTO: ${monto} | STRIPE\n")
            
            logger.info(f"✅ Pago registrado: {email} - ${monto}")
            
            # Notificación Telegram
            try:
                enviar_notificacion_pago_telegram(usuario, codigo, monto)
            except Exception as e:
                logger.error(f"Error enviando Telegram: {e}")
            
            return {
                "exitoso": True,
                "mensaje": f"Pago confirmado correctamente. Monto: ${monto}."
            }
        
        return {"status": "ok", "event": event["type"]}
        
    except Exception as e:
        logger.error(f"Error en webhook Stripe: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.get("/estado-pago/{codigo}")
async def estado_pago(codigo: str):
    """
    Verifica si un código ya pagó
    """
    usuario = obtener_usuario_por_codigo(codigo)
    
    if not usuario:
        return {"exitoso": False, "mensaje": "Código no encontrado"}
    
    return {
        "exitoso": True,
        "pagado": usuario.get("pagado", False),
        "email": usuario.get("email")
    }

@router.get("/pago-exitoso")
async def pago_exitoso(request: Request, session_id: str = None):
    """
    Página de éxito después del pago
    """
    return templates.TemplateResponse("pago_exitoso.html", {
        "request": request,
        "session_id": session_id,
        "mensaje": "¡Pago completado exitosamente! Ahora puedes lanzar el escaneo."
    })

@router.get("/pago-cancelado")
async def pago_cancelado(request: Request, session_id: str = None):
    """
    Página de cancelación
    """
    return templates.TemplateResponse("pago_cancelado.html", {
        "request": request,
        "session_id": session_id,
        "mensaje": "El pago fue cancelado. Puedes intentarlo nuevamente cuando quieras."
    })
=======

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
>>>>>>> dev
