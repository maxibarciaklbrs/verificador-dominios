# app/services/telegram_service.py
import logging
import requests
import string
import random
from datetime import datetime
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

def enviar_telegram(mensaje: str) -> bool:
    """Envía mensaje a Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Telegram no configurado")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Mensaje de Telegram enviado")
            return True
        else:
            logger.error(f"❌ Error Telegram: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error enviando Telegram: {e}")
        return False


def enviar_notificacion_pago_telegram(datos: dict, codigo: str, monto: float) -> bool:
    """Envía notificación de pago por Telegram"""
    transaccion_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    codigo_verificacion = ''.join(random.choices(string.digits, k=6))
    
    mensaje = f"""
🔔 <b>NUEVO PAGO RECIBIDO - klbrs.es</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 <b>DATOS DEL CLIENTE</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 <b>Cliente:</b> {datos.get('nombre', 'N/A')} {datos.get('apellido', 'N/A')}
📧 <b>Email:</b> {datos.get('email', 'N/A')}
🌐 <b>Dominio:</b> {datos.get('dominio', 'N/A')}
🔐 <b>Código verif.:</b> <code>{codigo}</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 <b>DETALLES DEL PAGO</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 <b>Monto:</b> ${monto} USD
🆔 <b>Transacción ID:</b> <code>{transaccion_id}</code>
✅ <b>Código verificación:</b> <code>{codigo_verificacion}</code>
📅 <b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ <b>Estado:</b> PAGO CONFIRMADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<i>Notificación automática - Sistema klbrs.es</i>
    """
    
    return enviar_telegram(mensaje)
