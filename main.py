from fastapi import FastAPI, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
import secrets
import string
import json

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configuración SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "reseller2.networksclub.net")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
MI_EMAIL = os.getenv("MI_EMAIL", SMTP_USER)

# ============================================
# FILTRO DE EMAILS GRATUITOS
# ============================================

# Lista de dominios gratuitos a bloquear
DOMINIOS_BLOQUEADOS = [
    'gmail', 'googlemail',
    'hotmail', 'outlook', 'live', 'msn',
    'yahoo', 'ymail', 'rocketmail',
    'protonmail', 'proton', 'mail', 'gmx',
    'aol', 'icloud', 'me', 'mac', 'yandex',
    'mailinator', 'tempmail', 'guerrillamail'
]

def email_es_gratuito(email: str):
    """
    Verifica si un email es de servicios gratuitos
    Retorna: (es_bloqueado, mensaje)
    """
    try:
        dominio = email.split('@')[1].lower()
    except:
        return True, "Email inválido"
    
    parte_principal = dominio.split('.')[0]
    
    for bloqueado in DOMINIOS_BLOQUEADOS:
        if bloqueado in dominio or parte_principal == bloqueado:
            return True, f"No se permiten emails de {bloqueado}. Usa un email corporativo."
    
    return False, ""

# ============================================
# GENERADOR DE CÓDIGO ALEATORIO
# ============================================
def generar_codigo_verificacion(longitud: int = 43) -> str:
    """
    Genera un código aleatorio criptográficamente seguro.
    Incluye: Aa-Zz, 0-9, "-", "_"
    """
    # Definimos el alfabeto solicitado
    caracteres = string.ascii_letters + string.digits + "-_"
    
    # Usamos secrets para una generación segura a nivel criptográfico
    codigo = ''.join(secrets.choice(caracteres) for _ in range(longitud))
    return codigo



"""
def generar_codigo_verificacion(longitud: int = 43) -> str:
    caracteres = string.ascii_letters + string.digits
    codigo = ''.join(secrets.choice(caracteres) for _ in range(longitud))
    return codigo
"""
# ============================================
# GESTIÓN DE VERIFICACIONES PENDIENTES
# ============================================

ARCHIVO_PENDIENTES = "pendientes_verificacion.json"

def guardar_codigo_pendiente(email: str, codigo: str, nombre: str, apellido: str):
    """
    Guarda el código pendiente de verificación con fecha de expiración
    """
    pendientes = {}
    if os.path.exists(ARCHIVO_PENDIENTES):
        with open(ARCHIVO_PENDIENTES, "r", encoding="utf-8") as f:
            pendientes = json.load(f)
    
    pendientes[email] = {
        "codigo": codigo,
        "nombre": nombre,
        "apellido": apellido,
        "fecha_registro": datetime.now().isoformat(),
        "fecha_expiracion": (datetime.now() + timedelta(days=7)).isoformat(),
        "verificado": False
    }
    
    with open(ARCHIVO_PENDIENTES, "w", encoding="utf-8") as f:
        json.dump(pendientes, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Código guardado para {email} - Expira en 7 días")

# ============================================
# FUNCIÓN DE ENVÍO DE EMAIL CON CÓDIGO
# ============================================

def enviar_email_verificacion(nombre: str, apellido: str, email_usuario: str, codigo: str):
    """
    Envía un email con el código de verificación DNS
    """
    try:
        msg = EmailMessage()
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = email_usuario
        msg['Subject'] = f"🔐 Verifica tu dominio - {nombre} {apellido}"
        
        contenido = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    VERIFICACIÓN DE DOMINIO                        ║
╚══════════════════════════════════════════════════════════════════╝

Hola {nombre} {apellido},

Para completar tu registro, debes verificar que eres el propietario del dominio asociado a tu email: {email_usuario}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 CÓDIGO DE VERIFICACIÓN (43 caracteres)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{codigo}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 INSTRUCCIONES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Inicia sesión en el panel de control de tu dominio (cPanel, Cloudflare, etc.)
2. Crea un nuevo registro TXT en la zona DNS de tu dominio
3. En el campo "Nombre/Host", escribe: @ o tu dominio
4. En el campo "Valor/Contenido", pega EXACTAMENTE el código de arriba
5. Guarda los cambios
6. Espera unos minutos a que se propague el DNS (puede tomar hasta 24h)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 EJEMPLO DE REGISTRO TXT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tipo: TXT
Nombre: @
Valor: {codigo}
TTL: Automático o 3600

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❓ ¿POR QUÉ ESTO?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verificamos que eres el propietario legítimo del dominio.
Esto nos permite garantizar que solo usuarios con dominios válidos accedan.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ IMPORTANTE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Este código es único y personal
• No lo compartas con nadie
• Tienes 7 días para completar la verificación
• Una vez verificado, podrás acceder a todos los servicios

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 ¿Necesitas ayuda? Responde a este correo.

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

def enviar_email_admin(nombre: str, apellido: str, email_usuario: str, codigo: str):
    """
    Envía un email al administrador notificando nuevo registro
    """
    try:
        msg = EmailMessage()
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = MI_EMAIL
        msg['Subject'] = f"📋 Nuevo registro pendiente: {nombre} {apellido}"
        
        contenido = f"""
NUEVO REGISTRO PENDIENTE DE VERIFICACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Nombre completo: {nombre} {apellido}
• Email: {email_usuario}
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
    <title>Registro Corporativo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
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
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        .required {
            color: #e74c3c;
        }
        input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
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
        button:hover {
            transform: translateY(-2px);
        }
        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 8px;
            color: #666;
        }
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
                <label for="nombre">Nombre <span class="required">*</span></label>
                <input type="text" id="nombre" name="nombre" required placeholder="Tu nombre">
            </div>
            <div class="form-group">
                <label for="apellido">Apellido <span class="required">*</span></label>
                <input type="text" id="apellido" name="apellido" required placeholder="Tu apellido">
            </div>
            <div class="form-group">
                <label for="email">Email Corporativo <span class="required">*</span></label>
                <input type="email" id="email" name="email" required placeholder="nombre@tuempresa.com">
            </div>
            <button type="submit">Enviar ✨</button>
        </form>
        <div id="loading" class="loading">Validando email...</div>
        <div class="warning">
            ⚠️ No se permiten emails gratuitos (Gmail, Hotmail, Yahoo, Outlook, etc.)
        </div>
    </div>
    <script>
        const dominiosGratuitos = ['gmail', 'googlemail', 'hotmail', 'outlook', 'live', 'msn', 'yahoo', 'ymail', 'rocketmail', 'protonmail', 'proton', 'mail', 'gmx', 'aol', 'icloud', 'me', 'mac'];
        
        document.getElementById('registroForm').addEventListener('submit', function(e) {
            const email = document.getElementById('email').value;
            const dominio = email.split('@')[1];
            
            if (dominio) {
                const partePrincipal = dominio.split('.')[0].toLowerCase();
                if (dominiosGratuitos.includes(partePrincipal)) {
                    e.preventDefault();
                    alert('❌ No se permiten emails gratuitos. Usa un email corporativo.');
                    document.getElementById('loading').style.display = 'none';
                    document.querySelector('button').disabled = false;
                    return false;
                }
            }
            
            document.getElementById('loading').style.display = 'block';
            document.querySelector('button').disabled = true;
        });
    </script>
</body>
</html>
"""

# ============================================
# HTML DE CONFIRMACIÓN CON CÓDIGO
# ============================================

def generar_html_confirmacion(nombre: str, apellido: str, email: str, codigo: str):
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verificación Requerida</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
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
            max-width: 550px;
            width: 100%;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .success-icon {{
            font-size: 80px;
            color: #28a745;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        p {{
            color: #666;
            margin-bottom: 20px;
            line-height: 1.6;
        }}
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
            font-size: 16px;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            word-break: break-all;
        }}
        .btn-back {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border-radius: 10px;
            text-decoration: none;
        }}
        .btn-back:hover {{
            transform: translateY(-2px);
        }}
    </style>
</head>
<body>
    <div class="success-card">
        <div class="success-icon">🔐</div>
        <h1>¡Verificación Requerida!</h1>
        <p>Hemos enviado un email a <strong>{email}</strong> con instrucciones para verificar tu dominio.</p>
        
        <div class="info-box">
            <strong>📝 ¿Qué debes hacer?</strong><br><br>
            1. Revisa tu bandeja de entrada (y spam)<br>
            2. Copia el código de verificación de 32 caracteres<br>
            3. Crea un registro TXT en tu DNS con ese código<br>
            4. Espera la propagación (minutos a horas)<br>
            5. Tu dominio quedará verificado
        </div>
        
        <div class="codigo-box">
            <strong>Código de verificación:</strong><br>
            {codigo}
        </div>
        
        <p style="font-size: 14px;">⚠️ Guarda este código. Expira en 7 días.</p>
        
        <a href="/" class="btn-back">← Volver al inicio</a>
    </div>
</body>
</html>
    """

# ============================================
# ENDPOINTS
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
    # VALIDAR QUE NO SEA EMAIL GRATUITO
    es_bloqueado, mensaje = email_es_gratuito(email)
    
    if es_bloqueado:
        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Email no permitido</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 20px;
                }}
                .error-card {{
                    background: white;
                    border-radius: 20px;
                    padding: 40px;
                    max-width: 450px;
                    text-align: center;
                }}
                .error-icon {{ font-size: 80px; color: #e74c3c; }}
                h1 {{ color: #333; margin-bottom: 10px; }}
                .btn-back {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 12px 30px;
                    border-radius: 10px;
                    text-decoration: none;
                    display: inline-block;
                }}
            </style>
        </head>
        <body>
            <div class="error-card">
                <div class="error-icon">⛔</div>
                <h1>Email no permitido</h1>
                <p>{mensaje}</p>
                <a href="/" class="btn-back">← Volver</a>
            </div>
        </body>
        </html>
        """
    
    # Generar código de verificación de 32 caracteres
    codigo_verificacion = generar_codigo_verificacion()
    
    # Guardar código pendiente
    guardar_codigo_pendiente(email, codigo_verificacion, nombre, apellido)
    
    # Enviar email al usuario con el código (fondo)
    background_tasks.add_task(enviar_email_verificacion, nombre, apellido, email, codigo_verificacion)
    
    # Enviar notificación al administrador (fondo)
    background_tasks.add_task(enviar_email_admin, nombre, apellido, email, codigo_verificacion)
    
    # Guardar en archivo local
    with open("registros.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp} | {nombre} {apellido} | {email} | CODIGO: {codigo_verificacion} | PENDIENTE\n")
    
    # Mostrar confirmación con el código
    return generar_html_confirmacion(nombre, apellido, email, codigo_verificacion)

