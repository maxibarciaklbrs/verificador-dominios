from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.models import obtener_usuario_por_codigo, marcar_pagado
from app.services.telegram_service import enviar_notificacion_pago_telegram
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook-pago")
async def webhook_pago(request: Request):
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
        f.write(f"{datetime.now().isoformat()} | {email} | {usuario['nombre']} | {usuario['apellido']} | CODIGO: {codigo} | MONTO: ${monto}\n")
    
    logger.info(f"Pago registrado: {email} - ${monto}")
    
    # Notificación Telegram
    try:
        enviar_notificacion_pago_telegram(usuario, codigo, monto)
    except Exception as e:
        logger.error(f"Error enviando Telegram: {e}")
    
    return {
        "exitoso": True,
        "mensaje": f"Pago confirmado correctamente. Monto: ${monto}. Nos pondremos en contacto contigo pronto."
    }
