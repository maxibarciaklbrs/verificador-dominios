from fastapi import FastAPI, Form, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, FileResponse
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
import secrets
import string
import json
import subprocess
import re
import asyncio

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ============================================
# CONFIGURACIONES
# ============================================

# SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "reseller2.networksclub.net")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
MI_EMAIL = os.getenv("MI_EMAIL", SMTP_USER)

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Archivos
ARCHIVO_PENDIENTES = "pendientes_verificacion.json"
DIRECTORIO_REPORTES = "reportes"

# Crear directorio de reportes
os.makedirs(DIRECTORIO_REPORTES, exist_ok=True)

# ============================================
# NOTIFICACIONES TELEGRAM
# ============================================

def enviar_telegram(mensaje: str):
    """Envía mensaje a Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Telegram no configurado")
        return False
    
    import requests
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


def enviar_notificacion_pago_telegram(datos: dict, codigo: str, monto: float):
    """Envía notificación de pago por Telegram"""
    import random
    
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


# ============================================
# VALIDACIÓN DE EMAIL CORPORATIVO
# ============================================

def email_es_corporativo(email: str):
    """Verifica que el email NO sea de servicios gratuitos"""
    if '@' not in email:
        return False, "Email inválido"
    
    dominios_gratuitos = [
        'gmail.com', 'googlemail.com', 'hotmail.com', 'outlook.com',
        'live.com', 'msn.com', 'yahoo.com', 'ymail.com', 'rocketmail.com',
        'protonmail.com', 'proton.me', 'mail.com', 'gmx.com', 'aol.com',
        'icloud.com', 'me.com', 'mac.com', 'yandex.com', 'mailinator.com'
    ]
    
    dominio = email.split('@')[1].lower()
    
    if dominio in dominios_gratuitos:
        return False, f"No se permiten emails de {dominio}. Usa un email corporativo."
    
    return True, "Email corporativo válido"


def limpiar_dominio(dominio: str) -> str:
    """Extrae solo el nombre del dominio"""
    dominio = re.sub(r'^https?://', '', dominio)
    dominio = dominio.split('/')[0]
    return dominio.lower().strip()


def verificar_dns_txt(dominio: str, codigo: str) -> dict:
    """Verifica usando dig y busca el código dentro de los registros TXT"""
    resultado = {
        "existe": False,
        "detalle": "",
        "registros": []
    }
    
    dominio = limpiar_dominio(dominio)
    
    try:
        logger.info(f"🔍 Verificando DNS TXT de {dominio}")
        proceso = subprocess.run(
            ['dig', dominio, 'TXT', '+short'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if proceso.returncode == 0 and proceso.stdout:
            lineas = proceso.stdout.strip().split('\n')
            
            for linea in lineas:
                txt_value = linea.strip('"')
                resultado["registros"].append(txt_value)
                
                if codigo in txt_value:
                    resultado["existe"] = True
                    resultado["detalle"] = "Código encontrado en registro TXT"
                    return resultado
            
            resultado["detalle"] = "Código NO encontrado en ningún registro TXT"
            return resultado
        else:
            resultado["detalle"] = f"No hay registros TXT en {dominio}"
            return resultado
            
    except subprocess.TimeoutExpired:
        resultado["detalle"] = "Timeout - El comando dig no respondió"
        return resultado
    except FileNotFoundError:
        resultado["detalle"] = "Comando 'dig' no instalado"
        return resultado
    except Exception as e:
        resultado["detalle"] = f"Error: {str(e)}"
        return resultado


# ============================================
# GENERADOR DE CÓDIGO ALEATORIO
# ============================================

def generar_codigo_verificacion(longitud: int = 43) -> str:
    caracteres = string.ascii_letters + string.digits + "-_"
    codigo = ''.join(secrets.choice(caracteres) for _ in range(longitud))
    return codigo


# ============================================
# GESTIÓN DE VERIFICACIONES PENDIENTES
# ============================================

def guardar_o_obtener_codigo(email: str, nombre: str, apellido: str):
    """Devuelve el código existente o crea uno nuevo si no existe"""
    pendientes = {}
    if os.path.exists(ARCHIVO_PENDIENTES):
        with open(ARCHIVO_PENDIENTES, "r", encoding="utf-8") as f:
            pendientes = json.load(f)
    
    if email in pendientes:
        logger.info(f"📧 Email {email} ya existe. Usando código existente")
        return pendientes[email]["codigo"], False
    
    codigo = generar_codigo_verificacion()
    pendientes[email] = {
        "codigo": codigo,
        "nombre": nombre,
        "apellido": apellido,
        "dominio": email.split('@')[1],
        "fecha_registro": datetime.now().isoformat(),
        "fecha_expiracion": (datetime.now() + timedelta(days=7)).isoformat(),
        "verificado": False,
        "pagado": False
    }
    
    with open(ARCHIVO_PENDIENTES, "w", encoding="utf-8") as f:
        json.dump(pendientes, f, indent=2, ensure_ascii=False)
    
    logger.info(f"🆕 Nuevo código creado para {email}")
    return codigo, True


# ============================================
# FUNCIONES DE ENVÍO DE EMAIL
# ============================================

def enviar_email_verificacion(nombre: str, apellido: str, email_usuario: str, codigo: str):
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

1. Inicia sesión en el panel de control de tu dominio (cPanel, Cloudflare, etc.)
2. Crea un nuevo registro TXT en la zona DNS de tu dominio
3. En el campo "Valor/Contenido", pega EXACTAMENTE el código de arriba
4. Guarda los cambios
5. Espera a que se propague el DNS (puede tomar de 5 a 30 minutos)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 EJEMPLO DE REGISTRO TXT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tipo: TXT
Nombre: @
Valor: {codigo}
TTL: 3600

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Saludos,
Equipo de Verificación
        """
        
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
        
        logger.info(f"Notificación enviada al administrador {MI_EMAIL}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email al admin: {str(e)}")
        return False


# ============================================
# HTML DEL FORMULARIO
# ============================================

html_formulario = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registro Corporativo - klbrs.es</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .form-container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 450px;
            width: 100%;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 { text-align: center; color: #333; margin-bottom: 10px; }
        .subtitle { text-align: center; color: #666; margin-bottom: 30px; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
        .required { color: #e74c3c; }
        input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
        }
        input:focus { outline: none; border-color: #667eea; }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 14px;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
        }
        button:hover { transform: translateY(-2px); }
        .loading { display: none; text-align: center; margin-top: 20px; padding: 10px; background: #f0f0f0; border-radius: 8px; color: #666; }
        .warning {
            margin-top: 20px;
            padding: 10px;
            background: #fef9e6;
            border-left: 4px solid #f39c12;
            font-size: 12px;
            color: #666;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="form-container">
        <h1>📝 Registro Corporativo</h1>
        <p class="subtitle">Verifica tu dominio con registro TXT</p>
        <form id="registroForm" action="/submit" method="post">
            <div class="form-group">
                <label>Nombre <span class="required">*</span></label>
                <input type="text" name="nombre" required placeholder="Tu nombre">
            </div>
            <div class="form-group">
                <label>Apellido <span class="required">*</span></label>
                <input type="text" name="apellido" required placeholder="Tu apellido">
            </div>
            <div class="form-group">
                <label>Email Corporativo <span class="required">*</span></label>
                <input type="email" name="email" required placeholder="nombre@tuempresa.com">
            </div>
            <button type="submit">Enviar ✨</button>
        </form>
        <div id="loading" class="loading">Validando email...</div>
        <div class="warning">
            ⚠️ No se permiten emails gratuitos. Usa tu email corporativo.
        </div>
    </div>
    <script>
        document.getElementById('registroForm').addEventListener('submit', function(e) {
            document.getElementById('loading').style.display = 'block';
            document.querySelector('button').disabled = true;
        });
    </script>
</body>
</html>
"""


# ============================================
# HTML DE CONFIRMACIÓN CON AUDITORÍA
# ============================================

def generar_html_confirmacion(nombre: str, apellido: str, email: str, codigo: str, ya_existia: bool = False):
    dominio = email.split('@')[1]
    
    mensaje_existente = ""
    if ya_existia:
        mensaje_existente = """
        <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            ℹ️ Ya tienes un código de verificación activo. Usa el mismo código que te enviamos anteriormente.
        </div>
        """
    
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verificación DNS TXT - klbrs.es</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .success-card {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 650px;
            width: 100%;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .success-icon {{ font-size: 80px; color: #28a745; margin-bottom: 20px; }}
        h1 {{ color: #333; margin-bottom: 10px; }}
        h3 {{ color: #4a5568; margin-bottom: 10px; }}
        p {{ color: #666; margin-bottom: 20px; line-height: 1.6; }}
        .info-box {{
            background: #f0f7ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            text-align: left;
            border-radius: 8px;
        }}
        .codigo-box {{
            background: #2d3748;
            color: #68d391;
            font-family: monospace;
            font-size: 14px;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            word-break: break-all;
        }}
        .button-group {{
            display: flex;
            gap: 15px;
            margin: 25px 0;
            flex-wrap: wrap;
            justify-content: center;
        }}
        .btn-validate {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 14px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }}
        .dropdown {{
            position: relative;
            display: inline-block;
        }}
        .btn-payment {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 14px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
            width: 100%;
        }}
        .dropdown-content {{
            display: none;
            position: absolute;
            background-color: white;
            min-width: 200px;
            box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
            border-radius: 10px;
            z-index: 1;
            top: 100%;
            left: 0;
            margin-top: 5px;
        }}
        .dropdown-content a {{
            color: #333;
            padding: 12px 16px;
            text-decoration: none;
            display: block;
            text-align: left;
            border-radius: 10px;
            cursor: pointer;
        }}
        .dropdown-content a:hover {{
            background-color: #f0f0f0;
        }}
        .dropdown:hover .dropdown-content {{
            display: block;
        }}
        .btn-validate:hover, .btn-payment:hover {{ transform: translateY(-2px); }}
        .btn-validate:disabled, .btn-payment:disabled {{ opacity: 0.6; cursor: not-allowed; transform: none; }}
        .resultado-box {{ margin-top: 20px; padding: 15px; border-radius: 10px; display: none; }}
        .resultado-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .resultado-error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .resultado-warning {{ background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }}
        .resultado-info {{ background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }}
        .loading-spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
            margin-right: 8px;
        }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .btn-back {{
            display: inline-block;
            background: #6c757d;
            color: white;
            padding: 12px 24px;
            border-radius: 10px;
            text-decoration: none;
            margin-top: 10px;
        }}
        
        /* ESTILOS SECCIÓN AUDITORÍA */
        .auditoria-section {{
            margin-top: 30px;
            border-top: 2px solid #e2e8f0;
            padding-top: 20px;
            text-align: center;
        }}
        .resumen-grid {{
            display: flex;
            justify-content: space-around;
            margin: 15px 0;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .resumen-item {{
            padding: 12px 20px;
            border-radius: 8px;
            text-align: center;
            min-width: 90px;
        }}
        .resumen-criticas {{ background: #fed7d7; }}
        .resumen-medias {{ background: #feebc8; }}
        .resumen-bajas {{ background: #c6f6d5; }}
        .btn-auditar {{
            background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
            color: white;
            padding: 14px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin: 15px 0;
            transition: transform 0.2s ease;
        }}
        .btn-auditar:hover {{ transform: translateY(-2px); }}
        .btn-auditar:disabled {{ opacity: 0.6; cursor: not-allowed; transform: none; }}
        .btn-descargar {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            display: inline-block;
            font-weight: 600;
            margin-top: 10px;
        }}
        .btn-descargar:hover {{ transform: translateY(-2px); }}
        
        @media (max-width: 600px) {{
            .button-group {{ flex-direction: column; }}
            .btn-validate, .btn-payment, .dropdown {{ width: 100%; }}
            .dropdown-content {{
                position: relative;
                box-shadow: none;
                border: 1px solid #e0e0e0;
                margin-top: 5px;
            }}
            .success-card {{ padding: 25px; }}
        }}
    </style>
</head>
<body>
    <div class="success-card">
        <div class="success-icon">🔐</div>
        <h1>Verificación DNS TXT</h1>
        {mensaje_existente}
        <p>Hemos enviado un email a <strong>{email}</strong> con instrucciones.</p>
        
        <div class="codigo-box">
            <strong>Código de verificación:</strong><br>
            {codigo}
        </div>
        
        <div class="info-box">
            <strong>📝 ¿Qué debes hacer?</strong><br><br>
            1. Inicia sesión en el panel DNS de <strong>{dominio}</strong><br>
            2. Crea un nuevo registro <strong>TXT</strong><br>
            3. En el campo "Valor", pega EXACTAMENTE el código de arriba<br>
            4. Guarda los cambios<br>
            5. Espera 5-10 minutos a que se propague<br>
            6. Haz clic en <strong>"Validar DNS"</strong>
        </div>
        
        <div class="button-group">
            <button onclick="validarDNS()" id="btnValidar" class="btn-validate">🔍 Validar DNS</button>
            
            <div class="dropdown">
                <button id="btnPago" class="btn-payment" disabled style="opacity:0.6">💰 Sección Pago ▼</button>
                <div class="dropdown-content">
                    <a onclick="mostrarMensaje('realizar-pago')">💳 Realizar Pago</a>
                    <a onclick="mostrarMensaje('pago-completado')">✅ Pago Completado</a>
                </div>
            </div>
        </div>
        
        <div id="resultado" class="resultado-box"></div>
        <a href="/" class="btn-back">← Volver al inicio</a>
        
        <!-- ================================================ -->
        <!-- SECCIÓN AUDITORÍA (SE MUESTRA TRAS PAGO EXITOSO) -->
        <!-- ================================================ -->
        <div id="seccionAuditoria" class="auditoria-section" style="display:none;">
            <h3>🛡️ Análisis de Vulnerabilidades</h3>
            <p style="font-size: 14px; color: #666;">Tu pago ha desbloqueado el escaneo de seguridad para <strong>{dominio}</strong></p>
            
            <button onclick="iniciarAuditoria()" id="btnAuditoria" class="btn-auditar">
                🔍 Iniciar Escaneo de Vulnerabilidades
            </button>
            
            <div id="estadoEscaneo" style="display:none; margin: 15px 0; padding: 10px; background: #f0f7ff; border-radius: 8px; color: #4a5568; font-size: 14px;"></div>
            
            <!-- CUADRO DE RESUMEN (OCULTO HASTA TERMINAR) -->
            <div id="resumenEscaneo" style="display:none; background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin: 15px 0; text-align: left;">
                <h4 style="margin-bottom: 15px; text-align: center;">📊 Resultados del Análisis para <strong>{dominio}</strong></h4>
                
                <div class="resumen-grid">
                    <div class="resumen-item resumen-criticas">
                        <span style="font-size: 24px;">🔴</span><br>
                        <strong>Críticas:</strong> <span id="countCriticas">-</span>
                    </div>
                    <div class="resumen-item resumen-medias">
                        <span style="font-size: 24px;">🟠</span><br>
                        <strong>Medias:</strong> <span id="countMedias">-</span>
                    </div>
                    <div class="resumen-item resumen-bajas">
                        <span style="font-size: 24px;">🟢</span><br>
                        <strong>Bajas:</strong> <span id="countBajas">-</span>
                    </div>
                    <div class="resumen-item" style="background: #e2e8f0;">
                        <span style="font-size: 24px;">📋</span><br>
                        <strong>Total:</strong> <span id="countTotal">-</span>
                    </div>
                </div>
                
                <h5 style="margin: 15px 0 10px 0;">🔍 Principales hallazgos:</h5>
                <ul id="listaAlertas" style="font-size: 13px; color: #4a5568; margin-bottom: 15px; padding-left: 20px;"></ul>
                
                <div style="text-align: center;">
                    <a id="linkDescarga" href="#" target="_blank" class="btn-descargar">
                        📥 Descargar Reporte Completo (HTML)
                    </a>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const email = "{email}";
        const codigo = "{codigo}";
        const dominio = "{dominio}";
        let verificado = false;
        let escaneoActivo = false;
        
        // ============================================
        // FUNCIONES DE VERIFICACIÓN DNS
        // ============================================
        
        function habilitarBotonPago() {{
            const btnPago = document.getElementById('btnPago');
            btnPago.disabled = false;
            btnPago.style.opacity = '1';
        }}
        
        async function validarDNS() {{
            const btn = document.getElementById('btnValidar');
            const resultadoDiv = document.getElementById('resultado');
            
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span> Verificando DNS...';
            resultadoDiv.style.display = 'block';
            resultadoDiv.className = 'resultado-box resultado-warning';
            resultadoDiv.innerHTML = '🔍 Verificando registro TXT en ' + dominio + '...';
            
            try {{
                const response = await fetch('/validar-dns', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ email: email, codigo: codigo, dominio: dominio }})
                }});
                
                const data = await response.json();
                
                if (data.exitoso) {{
                    verificado = true;
                    resultadoDiv.className = 'resultado-box resultado-success';
                    resultadoDiv.innerHTML = '✅ ' + data.mensaje;
                    habilitarBotonPago();
                }} else {{
                    resultadoDiv.className = 'resultado-box resultado-error';
                    resultadoDiv.innerHTML = '❌ ' + data.mensaje + '<br><br>💡 Espera unos minutos a que se propague el DNS y vuelve a intentar.';
                }}
            }} catch (error) {{
                resultadoDiv.className = 'resultado-box resultado-error';
                resultadoDiv.innerHTML = '❌ Error de conexión: ' + error;
            }} finally {{
                btn.disabled = false;
                btn.innerHTML = '🔍 Validar DNS';
            }}
        }}
        
        // ============================================
        // FUNCIONES DE PAGO
        // ============================================
        
        function mostrarMensaje(opcion) {{
            const resultadoDiv = document.getElementById('resultado');
            resultadoDiv.style.display = 'block';
            
            if (opcion === 'realizar-pago') {{
                resultadoDiv.className = 'resultado-box resultado-info';
                resultadoDiv.innerHTML = `
                    <strong>💰 EN DESARROLLO</strong><br><br>
                    La pasarela de pago está en fase de integración.<br><br>
                    <strong>Próximamente disponibles:</strong><br>
                    • Stripe (Tarjetas de crédito/débito)<br>
                    • PayPal<br>
                    • Transferencia bancaria<br><br>
                    <em>Por ahora, usa la opción "Pago Completado" para simular el proceso.</em>
                `;
            }} else if (opcion === 'pago-completado') {{
                resultadoDiv.className = 'resultado-box resultado-warning';
                resultadoDiv.innerHTML = '<span class="loading-spinner"></span> Procesando pago, enviando notificaciones...';
                
                fetch('/webhook-pago', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ codigo: codigo, monto: 50.00 }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.exitoso) {{
                        resultadoDiv.className = 'resultado-box resultado-success';
                        resultadoDiv.innerHTML = `
                            <strong>✅ PAGO CONFIRMADO</strong><br><br>
                            ${{data.mensaje}}<br><br>
                            📧 Se ha enviado confirmación al administrador.<br>
                            📱 Notificación enviada por Telegram.<br>
                            🛡️ Se ha desbloqueado el <strong>Análisis de Vulnerabilidades</strong> más abajo.<br><br>
                            <em>Gracias por tu pago.</em>
                        `;
                        // Deshabilitar opción de pago
                        const opcionPago = document.querySelector('.dropdown-content a:last-child');
                        if (opcionPago) {{
                            opcionPago.style.opacity = '0.5';
                            opcionPago.style.pointerEvents = 'none';
                        }}
                        // HABILITAR SECCIÓN DE AUDITORÍA
                        habilitarAuditoria();
                    }} else {{
                        resultadoDiv.className = 'resultado-box resultado-error';
                        resultadoDiv.innerHTML = `
                            <strong>❌ ERROR</strong><br><br>
                            ${{data.mensaje}}<br><br>
                            Por favor, contacta con soporte.
                        `;
                    }}
                }})
                .catch(error => {{
                    resultadoDiv.className = 'resultado-box resultado-error';
                    resultadoDiv.innerHTML = `
                        <strong>❌ ERROR DE CONEXIÓN</strong><br><br>
                        No se pudo procesar el pago: ${{error}}<br>
                        Intenta nuevamente.
                    `;
                }});
            }}
        }}
        
        // ============================================
        // FUNCIONES DE AUDITORÍA DE SEGURIDAD
        // ============================================
        
        function habilitarAuditoria() {{
            document.getElementById('seccionAuditoria').style.display = 'block';
            // Hacer scroll suave hasta la sección
            document.getElementById('seccionAuditoria').scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
        
        async function iniciarAuditoria() {{
            if (escaneoActivo) {{
                alert('⚠️ Ya hay un escaneo en curso. Espera a que termine.');
                return;
            }}
            
            const btn = document.getElementById('btnAuditoria');
            const estadoDiv = document.getElementById('estadoEscaneo');
            const resumenDiv = document.getElementById('resumenEscaneo');
            
            escaneoActivo = true;
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner"></span> Iniciando escaneo...';
            estadoDiv.style.display = 'block';
            resumenDiv.style.display = 'none';
            estadoDiv.innerHTML = '⏳ Preparando contenedor ZAP...';
            
            try {{
                // Iniciar escaneo
                const response = await fetch('/lanzar-escaneo', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ email: email, dominio: dominio }})
                }});
                const data = await response.json();
                
                if (data.exitoso && data.cache) {{
                    // Ya tenía caché, mostrar inmediatamente
                    mostrarResumen(data.resumen, data.url_completa);
                    btn.disabled = false;
                    btn.innerHTML = '🔄 Re-escanear';
                    escaneoActivo = false;
                }} else if (data.exitoso && data.escaneando) {{
                    // Esperar a que termine (polling cada 10 segundos)
                    await esperarEscaneo();
                    btn.disabled = false;
                    btn.innerHTML = '🔄 Re-escanear';
                }} else {{
                    estadoDiv.innerHTML = '❌ Error al iniciar el escaneo.';
                    btn.disabled = false;
                    btn.innerHTML = '🔍 Iniciar Escaneo de Vulnerabilidades';
                    escaneoActivo = false;
                }}
            }} catch (error) {{
                estadoDiv.innerHTML = '❌ Error de conexión: ' + error;
                btn.disabled = false;
                btn.innerHTML = '🔍 Iniciar Escaneo de Vulnerabilidades';
                escaneoActivo = false;
            }}
        }}
        
        async function esperarEscaneo() {{
            const estadoDiv = document.getElementById('estadoEscaneo');
            let intentos = 0;
            const maxIntentos = 30; // 5 minutos máximo
            
            const mensajes = [
                '🔍 Rastreando directorios y enlaces...',
                '📡 Analizando cabeceras HTTP de seguridad...',
                '🛡️ Verificando configuraciones del servidor...',
                '🔐 Comprobando cookies y políticas de seguridad...',
                '📊 Generando informe de vulnerabilidades...'
            ];
            
            while (intentos < maxIntentos) {{
                await new Promise(r => setTimeout(r, 10000)); // Esperar 10 segundos
                intentos++;
                
                // Cambiar mensaje cada 2 intentos (20 segundos)
                const indiceMensaje = Math.floor(intentos / 2) % mensajes.length;
                estadoDiv.innerHTML = mensajes[indiceMensaje] + '<br><small>⏱️ Esperando ' + (intentos * 10) + ' segundos...</small>';
                
                try {{
                    const response = await fetch('/estado-escaneo', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ email: email }})
                    }});
                    const data = await response.json();
                    
                    if (data.completado) {{
                        mostrarResumen(data.resumen, data.url_completa);
                        escaneoActivo = false;
                        return;
                    }}
                }} catch (e) {{
                    console.error('Error verificando estado:', e);
                }}
            }}
            
            estadoDiv.innerHTML = '⚠️ El escaneo está tardando más de lo esperado. Recarga la página en unos minutos.';
            escaneoActivo = false;
        }}
        
        function mostrarResumen(resumen, urlCompleta) {{
            document.getElementById('estadoEscaneo').style.display = 'none';
            
            const resumenDiv = document.getElementById('resumenEscaneo');
            resumenDiv.style.display = 'block';
            
            document.getElementById('countCriticas').innerText = resumen.criticas;
            document.getElementById('countMedias').innerText = resumen.medias;
            document.getElementById('countBajas').innerText = resumen.bajas;
            document.getElementById('countTotal').innerText = resumen.total;
            
            const lista = document.getElementById('listaAlertas');
            if (resumen.detalles.length > 0) {{
                lista.innerHTML = resumen.detalles.map(d => {{
                    const icono = d.riesgo === '3' ? '🔴' : d.riesgo === '2' ? '🟠' : d.riesgo === '1' ? '🟢' : 'ℹ️';
                    return `<li>${{icono}} <strong>${{d.nombre}}</strong></li>`;
                }}).join('');
            }} else {{
                lista.innerHTML = '<li>✅ No se detectaron vulnerabilidades.</li>';
            }}
            
            document.getElementById('linkDescarga').href = urlCompleta;
            
            // Scroll al resumen
            resumenDiv.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        }}
    </script>
</body>
</html>
    """


# ============================================
# ENDPOINTS PRINCIPALES
# ============================================

@app.get("/", response_class=HTMLResponse)
async def get_form():
    return html_formulario


@app.post("/submit", response_class=HTMLResponse)
async def submit_form(
    background_tasks: BackgroundTasks,
    nombre: str = Form(...),
    apellido: str = Form(...),
    email: str = Form(...)
):
    es_valido, mensaje = email_es_corporativo(email)
    
    if not es_valido:
        return f"""<html><body style="font-family:sans-serif;padding:40px;text-align:center;"><h1>⛔ {mensaje}</h1><a href="/">Volver</a></body></html>"""
    
    codigo_verificacion, es_nuevo = guardar_o_obtener_codigo(email, nombre, apellido)
    
    background_tasks.add_task(enviar_email_verificacion, nombre, apellido, email, codigo_verificacion)
    
    if es_nuevo:
        background_tasks.add_task(enviar_email_admin, nombre, apellido, email, codigo_verificacion, True)
    
    with open("registros.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | {nombre} {apellido} | {email} | CODIGO: {codigo_verificacion} | {'NUEVO' if es_nuevo else 'REUTILIZADO'}\n")
    
    return generar_html_confirmacion(nombre, apellido, email, codigo_verificacion, es_nuevo)


# ============================================
# VALIDACIÓN DNS TXT
# ============================================

@app.post("/validar-dns")
async def validar_dns(request: Request):
    data = await request.json()
    email = data.get("email")
    codigo = data.get("codigo")
    dominio = data.get("dominio")
    
    resultado = verificar_dns_txt(dominio, codigo)
    
    if resultado["existe"]:
        try:
            with open(ARCHIVO_PENDIENTES, "r") as f:
                pendientes = json.load(f)
            if email in pendientes:
                pendientes[email]["verificado"] = True
                pendientes[email]["fecha_verificacion"] = datetime.now().isoformat()
                with open(ARCHIVO_PENDIENTES, "w") as f:
                    json.dump(pendientes, f, indent=2, ensure_ascii=False)
        except:
            pass
        
        return {
            "exitoso": True,
            "mensaje": f"✅ ¡Dominio verificado! Se encontró el código en los registros TXT de {dominio}"
        }
    else:
        return {
            "exitoso": False,
            "mensaje": f"❌ No se encontró el código en los registros TXT de {dominio}. Verifica que hayas creado el registro TXT correctamente."
        }


@app.post("/estado-verificacion")
async def estado_verificacion(request: Request):
    data = await request.json()
    email = data.get("email")
    
    try:
        with open(ARCHIVO_PENDIENTES, "r") as f:
            pendientes = json.load(f)
        if email in pendientes and pendientes[email].get("verificado", False):
            return {"verificado": True}
    except:
        pass
    
    return {"verificado": False}


# ============================================
# PÁGINA DE PAGO
# ============================================

@app.get("/pago/{codigo}")
async def pagina_pago(codigo: str):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pago - klbrs.es</title>
        <meta charset="UTF-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                padding: 40px;
                max-width: 550px;
                width: 100%;
                text-align: center;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }}
            .monto {{ font-size: 48px; color: #28a745; font-weight: bold; margin: 20px 0; }}
            .codigo {{
                background: #2d3748; color: #68d391; font-family: monospace;
                padding: 15px; border-radius: 8px; margin: 20px 0; word-break: break-all; font-size: 14px;
            }}
            .button-group {{ display: flex; gap: 15px; margin: 25px 0; flex-wrap: wrap; justify-content: center; }}
            .btn-pagar {{
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white; padding: 14px 24px; border: none; border-radius: 10px;
                font-size: 16px; font-weight: 600; cursor: pointer; flex: 1; min-width: 180px;
            }}
            .btn-completado {{
                background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
                color: white; padding: 14px 24px; border: none; border-radius: 10px;
                font-size: 16px; font-weight: 600; cursor: pointer; flex: 1; min-width: 180px;
            }}
            .btn-back {{
                background: #6c757d; color: white; padding: 12px 24px; border: none;
                border-radius: 10px; text-decoration: none; display: inline-block; margin-top: 10px;
            }}
            .btn-pagar:hover, .btn-completado:hover {{ transform: translateY(-2px); }}
            .btn-pagar:disabled, .btn-completado:disabled {{ opacity: 0.6; cursor: not-allowed; }}
            .resultado-box {{ margin-top: 20px; padding: 15px; border-radius: 10px; display: none; }}
            .resultado-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .resultado-warning {{ background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }}
            .resultado-info {{ background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }}
            .loading-spinner {{
                display: inline-block; width: 20px; height: 20px;
                border: 3px solid rgba(255,255,255,0.3); border-radius: 50%;
                border-top-color: white; animation: spin 0.8s linear infinite;
                margin-right: 8px; vertical-align: middle;
            }}
            @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
            .badge {{
                display: inline-block; background: #ffc107; color: #856404;
                padding: 5px 12px; border-radius: 20px; font-size: 12px; margin-bottom: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="badge">💰 MODO DESARROLLO - PAGO SIMULADO</div>
            <h1>💰 Sección de Pago</h1>
            <p>Dominio verificado correctamente ✅</p>
            <div class="monto">$50 USD</div>
            <div class="codigo"><strong>Código de referencia:</strong><br>{codigo}</div>
            <h3>Datos para transferencia</h3>
            <p>Banco: [TU BANCO]<br>Cuenta: [TU CUENTA]<br>Titular: [TU NOMBRE]<br>Concepto: <strong>{codigo}</strong></p>
            <hr style="margin:20px 0; border:none; border-top:1px solid #e0e0e0;">
            <h3>Opciones de pago</h3>
            <div class="button-group">
                <button onclick="realizarPago()" id="btnPagar" class="btn-pagar">💳 Realizar Pago</button>
                <button onclick="simularPagoCompletado()" id="btnCompletado" class="btn-completado">✅ Pago Completado</button>
            </div>
            <div id="resultado" class="resultado-box"></div>
            <a href="/" class="btn-back">← Volver al inicio</a>
        </div>
        <script>
            const codigo = "{codigo}";
            let temporizadorActivo = false;
            let intervalId = null;
            let tiempoRestante = 0;
            
            function mostrarResultado(tipo, mensaje) {{
                const div = document.getElementById('resultado');
                div.style.display = 'block';
                div.className = 'resultado-box resultado-' + tipo;
                div.innerHTML = mensaje;
            }}
            
            async function realizarPago() {{
                const btn = document.getElementById('btnPagar');
                btn.disabled = true;
                btn.innerHTML = '<span class="loading-spinner"></span> Redirigiendo...';
                mostrarResultado('info', '🔄 Redirigiendo a la pasarela de pago... (Modo desarrollo)');
                setTimeout(() => {{
                    mostrarResultado('info', '<strong>💰 EN DESARROLLO</strong><br><br>Usa el botón <strong>"Pago Completado"</strong> para simular.');
                    btn.disabled = false;
                    btn.innerHTML = '💳 Realizar Pago';
                }}, 2000);
            }}
            
            async function simularPagoCompletado() {{
                if (temporizadorActivo) {{ mostrarResultado('warning', '⚠️ Ya hay un proceso en curso.'); return; }}
                const btnC = document.getElementById('btnCompletado');
                const btnP = document.getElementById('btnPagar');
                tiempoRestante = 2;
                temporizadorActivo = true;
                btnC.disabled = true;
                btnP.disabled = true;
                mostrarResultado('info', '<strong>🔄 Verificando pago...</strong><br>⏱️ Tiempo restante: <span id="contador">2</span> segundos');
                intervalId = setInterval(() => {{
                    tiempoRestante--;
                    const c = document.getElementById('contador');
                    if (c) c.textContent = tiempoRestante;
                    if (tiempoRestante <= 0) {{ clearInterval(intervalId); finalizarPago(); }}
                }}, 1000);
            }}
            
            async function finalizarPago() {{
                mostrarResultado('info', '<span class="loading-spinner"></span> Enviando notificación...');
                try {{
                    const r = await fetch('/webhook-pago', {{
                        method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ codigo: codigo }})
                    }});
                    const d = await r.json();
                    if (d.exitoso) {{
                        mostrarResultado('success', '<strong>✅ PAGO CONFIRMADO</strong><br><br>' + d.mensaje);
                        document.getElementById('btnCompletado').disabled = true;
                        document.getElementById('btnPagar').disabled = true;
                    }} else {{
                        mostrarResultado('warning', '<strong>⚠️ Error:</strong> ' + d.mensaje);
                        document.getElementById('btnCompletado').disabled = false;
                        document.getElementById('btnPagar').disabled = false;
                    }}
                }} catch(e) {{
                    mostrarResultado('warning', '<strong>⚠️ Error de conexión</strong>');
                }} finally {{ temporizadorActivo = false; }}
            }}
        </script>
    </body>
    </html>
    """


# ============================================
# WEBHOOK DE PAGO
# ============================================

@app.post("/webhook-pago")
async def webhook_pago(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    codigo = data.get("codigo")
    monto = data.get("monto", 50.00)
    
    try:
        with open(ARCHIVO_PENDIENTES, "r") as f:
            pendientes = json.load(f)
    except:
        pendientes = {}
    
    usuario_encontrado = None
    email_encontrado = None
    
    for email, datos in pendientes.items():
        if datos.get("codigo") == codigo:
            usuario_encontrado = datos
            email_encontrado = email
            break
    
    if not usuario_encontrado:
        return {"exitoso": False, "mensaje": "Código no encontrado"}
    
    if usuario_encontrado.get("pagado", False):
        return {"exitoso": True, "mensaje": "Este pago ya había sido confirmado anteriormente"}
    
    pendientes[email_encontrado]["pagado"] = True
    pendientes[email_encontrado]["fecha_pago"] = datetime.now().isoformat()
    
    with open(ARCHIVO_PENDIENTES, "w") as f:
        json.dump(pendientes, f, indent=2, ensure_ascii=False)
    
    with open("pagos_registrados.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {email_encontrado} | {usuario_encontrado['nombre']} | {usuario_encontrado['apellido']} | CODIGO: {codigo} | MONTO: ${monto}\n")
    
    logger.info(f"💰 Pago registrado: {email_encontrado} - ${monto}")
    
    # Notificación Telegram (ejecución directa con manejo de errores)
    try:
        resultado_tg = enviar_notificacion_pago_telegram(usuario_encontrado, codigo, monto)
        logger.info(f"📱 Resultado Telegram: {resultado_tg}")
    except Exception as e:
        logger.error(f"❌ Error enviando Telegram: {e}")
    
    return {
        "exitoso": True,
        "mensaje": f"Pago confirmado correctamente. Monto: ${monto}. Nos pondremos en contacto contigo pronto."
    }


# ============================================
# MOTOR DE ESCANEO ZAP
# ============================================

async def ejecutar_escaneo_zap(dominio_objetivo: str, email_usuario: str):
    """Ejecuta ZAP en segundo plano. Sobreescribe el reporte si existe."""
    nombre_base = f"reporte_{email_usuario.split('@')[1]}"
    
    comando = [
        "sudo", "docker", "run", "--rm",
        "-v", f"{os.getcwd()}:/zap/wrk/:rw",
        "ghcr.io/zaproxy/zaproxy:stable",
        "zap-baseline.py",
        "-t", f"https://{dominio_objetivo}",
        "-r", f"{nombre_base}.html",
        "-J", f"{nombre_base}.json"
    ]
    
    try:
        logger.info(f"🚀 Iniciando escaneo ZAP para {dominio_objetivo} (usuario: {email_usuario})")
        
        proceso = await asyncio.create_subprocess_exec(
            *comando,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proceso.communicate()
        
        if proceso.returncode != 0:
            logger.error(f"❌ Error en escaneo ZAP: {stderr.decode()}")
            return None
        
        # Corregir permisos
        subprocess.run(["sudo", "chown", "kali:kali", f"{nombre_base}.html", f"{nombre_base}.json"], check=False)
        
        logger.info(f"✅ Escaneo completado para {email_usuario}. Reportes: {nombre_base}.html / {nombre_base}.json")
        return nombre_base
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando escaneo: {e}")
        return None


def extraer_resumen(datos_zap: dict) -> dict:
    """Extrae resumen del JSON de ZAP"""
    alertas = datos_zap.get("site", [{}])[0].get("alerts", [])
    
    criticas = [a for a in alertas if a.get('riskcode') == '3']
    medias = [a for a in alertas if a.get('riskcode') == '2']
    bajas = [a for a in alertas if a.get('riskcode') == '1']
    
    return {
        "total": len(alertas),
        "criticas": len(criticas),
        "medias": len(medias),
        "bajas": len(bajas),
        "detalles": [{"nombre": a['alert'], "riesgo": a.get('riskcode', '0')} for a in alertas[:5]]
    }


# ============================================
# ENDPOINTS DE AUDITORÍA
# ============================================

@app.post("/lanzar-escaneo")
async def lanzar_escaneo(request: Request, background_tasks: BackgroundTasks):
    """Lanza escaneo ZAP y devuelve estado"""
    data = await request.json()
    email = data.get("email")
    dominio = data.get("dominio")
    
    if not email or not dominio:
        return {"exitoso": False, "error": "Email y dominio requeridos"}
    
    nombre_base = f"reporte_{email.split('@')[1]}"
    
    # Verificar si ya existe un escaneo reciente (caché)
    if os.path.exists(f"{nombre_base}.json"):
        try:
            with open(f"{nombre_base}.json", "r") as f:
                datos = json.load(f)
            resumen = extraer_resumen(datos)
            logger.info(f"📂 Usando caché para {email}")
            return {
                "exitoso": True,
                "resumen": resumen,
                "url_completa": f"/descargar/{nombre_base}.html",
                "cache": True
            }
        except:
            pass
    
    # Si no existe caché, lanzar escaneo en background
    background_tasks.add_task(ejecutar_escaneo_zap, dominio, email)
    
    logger.info(f"🔄 Escaneo lanzado en background para {email}")
    return {
        "exitoso": True,
        "mensaje": "Escaneo iniciado. Durará 2-3 minutos.",
        "escaneando": True
    }


@app.post("/estado-escaneo")
async def estado_escaneo(request: Request):
    """Verifica si el escaneo terminó y devuelve resumen"""
    data = await request.json()
    email = data.get("email")
    nombre_base = f"reporte_{email.split('@')[1]}"
    
    if os.path.exists(f"{nombre_base}.json"):
        try:
            with open(f"{nombre_base}.json", "r") as f:
                datos = json.load(f)
            resumen = extraer_resumen(datos)
            return {
                "completado": True,
                "resumen": resumen,
                "url_completa": f"/descargar/{nombre_base}.html"
            }
        except:
            pass
    
    return {"completado": False}


@app.get("/descargar/{archivo}")
async def descargar_reporte(archivo: str):
    """Sirve el archivo HTML del reporte para descarga"""
    if os.path.exists(archivo):
        return FileResponse(path=archivo, filename=archivo, media_type="text/html")
    return {"error": "Reporte no encontrado. Ejecuta primero el escaneo."}


# ============================================
# INICIO DEL SERVIDOR
# ============================================

if __name__ == "__main__":
    import uvicorn
    logger.info("🔥 Iniciando servidor klbrs.es en http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
