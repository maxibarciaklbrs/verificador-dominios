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

load_dotenv()
logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Configurar Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# ============================================
# ENDPOINT LEGACY (SIMULACIÓN MANUAL)
# ============================================

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
