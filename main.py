from fastapi import FastAPI, Form, BackgroundTasks, Request
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
import subprocess
import re

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
# VALIDACIÓN DE EMAIL CORPORATIVO
# ============================================

def email_es_corporativo(email: str):
    """Verifica que el email NO sea de servicios gratuitos"""
    if '@' not in email:
        return False, "Email inválido"
    
    # Lista básica de dominios gratuitos
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
                    resultado["detalle"] = f"Código encontrado en registro TXT"
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
        resultado["detalle"] = "Comando 'dig' no instalado. Instala: sudo apt install dnsutils"
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

# ============================================
# GESTIÓN DE VERIFICACIONES PENDIENTES
# ============================================

ARCHIVO_PENDIENTES = "pendientes_verificacion.json"

def guardar_o_obtener_codigo(email: str, nombre: str, apellido: str):
    """
    Devuelve el código existente o crea uno nuevo si no existe
    Retorna: (codigo, es_nuevo)
    """
    pendientes = {}
    if os.path.exists(ARCHIVO_PENDIENTES):
        with open(ARCHIVO_PENDIENTES, "r", encoding="utf-8") as f:
            pendientes = json.load(f)
    
    # Si el email YA EXISTE, devolver el código existente
    if email in pendientes:
        logger.info(f"📧 Email {email} ya existe. Usando código existente: {pendientes[email]['codigo']}")
        return pendientes[email]["codigo"], False  # False = no es nuevo
    
    # Si es NUEVO, crear código
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
    
    logger.info(f"🆕 Nuevo código creado para {email}: {codigo}")
    return codigo, True  # True = es nuevo

# ============================================
# FUNCIÓN DE ENVÍO DE EMAIL CON CÓDIGO
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
    <title>Registro Corporativo</title>
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
# HTML DE CONFIRMACIÓN
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
    <title>Verificación DNS TXT</title>
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
            max-width: 600px;
            width: 100%;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .success-icon {{ font-size: 80px; color: #28a745; margin-bottom: 20px; }}
        h1 {{ color: #333; margin-bottom: 10px; }}
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
        }}
        .btn-validate:hover, .btn-payment:hover {{ transform: translateY(-2px); }}
        .btn-validate:disabled, .btn-payment:disabled {{ opacity: 0.6; cursor: not-allowed; }}
        .resultado-box {{ margin-top: 20px; padding: 15px; border-radius: 10px; display: none; }}
        .resultado-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .resultado-error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .resultado-warning {{ background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }}
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
        @media (max-width: 600px) {{
            .button-group {{ flex-direction: column; }}
            .btn-validate, .btn-payment {{ width: 100%; }}
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
            <strong>Código de verificación (43 caracteres):</strong><br>
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
            <button onclick="irPago()" id="btnPago" class="btn-payment" disabled style="opacity:0.6">💰 Sección Pago</button>
        </div>
        
        <div id="resultado" class="resultado-box"></div>
        <a href="/" class="btn-back">← Volver al inicio</a>
    </div>
    
    <script>
        const email = "{email}";
        const codigo = "{codigo}";
        const dominio = "{dominio}";
        let verificado = false;
        
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
                    const btnPago = document.getElementById('btnPago');
                    btnPago.disabled = false;
                    btnPago.style.opacity = '1';
                }} else {{
                    resultadoDiv.className = 'resultado-box resultado-error';
                    resultadoDiv.innerHTML = '❌ ' + data.mensaje + '<br><br>💡 Sugerencia: Espera unos minutos a que se propague el DNS y vuelve a intentar.';
                }}
            }} catch (error) {{
                resultadoDiv.className = 'resultado-box resultado-error';
                resultadoDiv.innerHTML = '❌ Error de conexión: ' + error;
            }} finally {{
                btn.disabled = false;
                btn.innerHTML = '🔍 Validar DNS';
            }}
        }}
        
        function irPago() {{
            if (!verificado) {{
                document.getElementById('resultado').style.display = 'block';
                document.getElementById('resultado').className = 'resultado-box resultado-warning';
                document.getElementById('resultado').innerHTML = '⚠️ Primero debes validar tu dominio con el registro TXT.';
                return;
            }}
            window.location.href = '/pago/' + encodeURIComponent(codigo);
        }}
    </script>
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
    # Validar email corporativo
    es_valido, mensaje = email_es_corporativo(email)
    
    if not es_valido:
        return f"""<html><body><h1>⛔ {mensaje}</h1><a href="/">Volver</a></body></html>"""
    
    # Obtener código existente o crear nuevo (SOLO ESTA LÍNEA)
    codigo_verificacion, es_nuevo = guardar_o_obtener_codigo(email, nombre, apellido)
    
    # Enviar email al usuario
    background_tasks.add_task(enviar_email_verificacion, nombre, apellido, email, codigo_verificacion)
    
    # Enviar notificación al admin solo si es nuevo
    if es_nuevo:
        background_tasks.add_task(enviar_email_admin, nombre, apellido, email, codigo_verificacion, True)
    
    # Guardar log
    with open("registros.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | {nombre} {apellido} | {email} | CODIGO: {codigo_verificacion} | {'NUEVO' if es_nuevo else 'REUTILIZADO'}\n")
    
    return generar_html_confirmacion(nombre, apellido, email, codigo_verificacion, es_nuevo)

# ============================================
# VALIDACIÓN DNS TXT (SOLO ESTE MÉTODO)
# ============================================

@app.post("/validar-dns")
async def validar_dns(request: Request):
    data = await request.json()
    email = data.get("email")
    codigo = data.get("codigo")
    dominio = data.get("dominio")
    
    # Verificar por DNS TXT
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


@app.get("/pago/{codigo}")
async def pagina_pago(codigo: str):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pago - klbrs.es</title>
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
                max-width: 500px;
                width: 100%;
                text-align: center;
            }}
            .monto {{ font-size: 48px; color: #28a745; font-weight: bold; margin: 20px 0; }}
            .codigo {{
                background: #2d3748;
                color: #68d391;
                font-family: monospace;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                word-break: break-all;
            }}
            button {{
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white;
                padding: 14px 30px;
                border: none;
                border-radius: 10px;
                font-size: 18px;
                cursor: pointer;
                width: 100%;
            }}
            .btn-back {{
                background: #6c757d;
                display: inline-block;
                text-decoration: none;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💰 Sección de Pago</h1>
            <p>Dominio verificado correctamente ✅</p>
            <div class="monto">$50 USD</div>
            <div class="codigo"><strong>Código:</strong><br>{codigo}</div>
            <h3>Datos para transferencia</h3>
            <p>Banco: [TU BANCO]<br>Cuenta: [TU CUENTA]<br>Concepto: <strong>{codigo}</strong></p>
            <button onclick="notificarPago()">✅ Ya realicé el pago</button>
            <a href="/" class="btn-back">← Volver</a>
            <div id="resultado" style="margin-top: 20px;"></div>
        </div>
        <script>
            async function notificarPago() {{
                const btn = event.target;
                btn.disabled = true;
                btn.textContent = 'Enviando...';
                try {{
                    const response = await fetch('/webhook-pago', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ codigo: '{codigo}' }})
                    }});
                    const data = await response.json();
                    document.getElementById('resultado').innerHTML = data.exitoso 
                        ? '<p style="color:green;">✅ ' + data.mensaje + '</p>'
                        : '<p style="color:red;">❌ ' + data.mensaje + '</p>';
                }} catch (error) {{
                    document.getElementById('resultado').innerHTML = '<p style="color:red;">❌ Error</p>';
                }}
                btn.disabled = false;
                btn.textContent = 'Reintentar';
            }}
        </script>
    </body>
    </html>
    """


@app.post("/webhook-pago")
async def webhook_pago(request: Request):
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
    
    pendientes[email_encontrado]["pagado"] = True
    pendientes[email_encontrado]["fecha_pago"] = datetime.now().isoformat()
    
    with open(ARCHIVO_PENDIENTES, "w") as f:
        json.dump(pendientes, f, indent=2, ensure_ascii=False)
    
    with open("pagos_registrados.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {email_encontrado} | {usuario_encontrado['nombre']} | {usuario_encontrado['apellido']} | CODIGO: {codigo} | MONTO: ${monto}\n")
    
    logger.info(f"💰 Pago registrado: {email_encontrado} - ${monto}")
    
    return {"exitoso": True, "mensaje": f"Pago notificado correctamente. Monto: ${monto}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
