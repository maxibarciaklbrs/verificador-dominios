# notifications.py
import smtplib
from email.message import EmailMessage
import logging
from datetime import datetime
import random
import string
import requests
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL, MI_EMAIL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

def enviar_email_verificacion(nombre: str, apellido: str, email_usuario: str, codigo: str):
    try:
        msg = EmailMessage()
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = email_usuario
        msg['Subject'] = f"🔐 Verifica tu dominio - {nombre} {apellido}"
        dominio = email_usuario.split('@')[1]
        contenido = f""" ... (mismo contenido que tenías) ... """
        msg.set_content(contenido)
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email de verificación enviado a {email_usuario}")
        return True
    except Exception as e:
        logger.error(f"Error enviando email: {str(e)}")
        return False

def enviar_email_admin(nombre: str, apellido: str, email_usuario: str, codigo: str, es_nuevo: bool = True):
    # similar a tu función original, usando las variables de config
    ...

def enviar_telegram(mensaje: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram no configurado")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error Telegram: {e}")
        return False

def enviar_notificacion_pago_telegram(datos: dict, codigo: str, monto: float):
    transaccion_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    codigo_verif = ''.join(random.choices(string.digits, k=6))
    mensaje = f"""🔔 <b>NUEVO PAGO RECIBIDO - klbrs.es</b>\n\n..."""  # igual que antes
    return enviar_telegram(mensaje)
