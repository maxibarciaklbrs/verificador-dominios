import smtplib
import logging
from email.message import EmailMessage
from datetime import datetime
from app.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    SMTP_FROM_EMAIL, MI_EMAIL
)

logger = logging.getLogger(__name__)


def enviar_email_verificacion(nombre: str, apellido: str, email_usuario: str, codigo: str) -> bool:
    """Envía email al usuario con instrucciones y código de verificación"""
    try:
        msg = EmailMessage()
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = email_usuario
        msg['Subject'] = f"🔐 Verifica tu dominio - {nombre} {apellido}"
        
        dominio = email_usuario.split('@')[1]
        
        contenido = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    VERIFICACIÓN DE DOMINIO                        ║
╚══════════════════════════════════════════════════════════════════╝

Hola {nombre} {apellido},

Para completar tu registro, debes verificar que eres el propietario del dominio: {dominio}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 CÓDIGO DE VERIFICACIÓN (43 caracteres)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{codigo}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 INSTRUCCIONES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Inicia sesión en el panel de control de tu dominio
2. Crea un nuevo registro TXT en la zona DNS
3. En el campo "Valor/Contenido", pega EXACTAMENTE el código
4. Guarda los cambios
5. Espera 5-30 minutos a que se propague el DNS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Saludos,
Equipo de Verificación
        """
        
        msg.set_content(contenido)
        
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Email de verificación enviado a {email_usuario}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enviando email: {str(e)}")
        return False


def enviar_email_admin(nombre: str, apellido: str, email_usuario: str, codigo: str, es_nuevo: bool = True) -> bool:
    """Envía notificación al administrador sobre nuevo registro o reenvío"""
    try:
        msg = EmailMessage()
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = MI_EMAIL
        msg['Subject'] = f"📋 {'Nuevo registro' if es_nuevo else 'Reenvío de código'} - {nombre} {apellido}"
        
        estado = "NUEVO REGISTRO" if es_nuevo else "REENVÍO DE CÓDIGO"
        
        contenido = f"""
{estado}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Nombre completo: {nombre} {apellido}
• Email: {email_usuario}
• Dominio: {email_usuario.split('@')[1]}
• Código de verificación: {codigo}
• Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
• Estado: PENDIENTE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
El usuario debe crear un registro TXT en su DNS con el código.
Expira en 7 días.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        msg.set_content(contenido)
        
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Notificación enviada al administrador {MI_EMAIL}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enviando email al admin: {str(e)}")
        return False
