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

# ============================================
# HTML DE CONFIRMACIÓN CON MENÚ DESPLEGABLE
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
        
        /* ============================================
           MENÚ DESPLEGABLE PARA SECCIÓN PAGO
        ============================================ */
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
            transition: background 0.2s ease;
            border-radius: 10px;
            cursor: pointer;
        }}
        
        .dropdown-content a:hover {{
            background-color: #f0f0f0;
        }}
        
        .dropdown:hover .dropdown-content {{
            display: block;
        }}
        
        .btn-payment:hover {{
            transform: translateY(-2px);
        }}
        
        .btn-validate:hover, .btn-payment:hover {{ transform: translateY(-2px); }}
        .btn-validate:disabled, .btn-payment:disabled {{ opacity: 0.6; cursor: not-allowed; transform: none; }}
        
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
            .btn-validate, .btn-payment, .dropdown {{ width: 100%; }}
            .dropdown-content {{
                position: relative;
                box-shadow: none;
                border: 1px solid #e0e0e0;
                margin-top: 5px;
            }}
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
            
            <!-- MENÚ DESPLEGABLE -->
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
    </div>
    
    <script>
        const email = "{email}";
        const codigo = "{codigo}";
        const dominio = "{dominio}";
        let verificado = false;
        
        // Habilitar botón de pago cuando se verifica el dominio
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
                    <em>Por ahora, el pago se gestiona de forma manual.</em>
                `;
            }} else if (opcion === 'pago-completado') {{
                resultadoDiv.className = 'resultado-box resultado-info';
                resultadoDiv.innerHTML = `
                    <strong>✅ PAGO COMPLETADO</strong><br><br>
                    Gracias por tu pago.<br>
                    Recibirás un email de confirmación en las próximas horas.<br><br>
                    <em>⚠️ En desarrollo: Esta opción enviará una notificación automática.</em>
                `;
            }}
            
            // Desaparecer después de 5 segundos
            setTimeout(() => {{
                resultadoDiv.style.display = 'none';
            }}, 5000);
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
            .monto {{
                font-size: 48px;
                color: #28a745;
                font-weight: bold;
                margin: 20px 0;
            }}
            .codigo {{
                background: #2d3748;
                color: #68d391;
                font-family: monospace;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                word-break: break-all;
                font-size: 14px;
            }}
            .button-group {{
                display: flex;
                gap: 15px;
                margin: 25px 0;
                flex-wrap: wrap;
                justify-content: center;
            }}
            .btn-pagar {{
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white;
                padding: 14px 24px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s ease;
                flex: 1;
                min-width: 180px;
            }}
            .btn-completado {{
                background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
                color: white;
                padding: 14px 24px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s ease;
                flex: 1;
                min-width: 180px;
            }}
            .btn-back {{
                background: #6c757d;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 10px;
                text-decoration: none;
                display: inline-block;
                margin-top: 10px;
            }}
            .btn-pagar:hover, .btn-completado:hover {{ transform: translateY(-2px); }}
            .btn-pagar:disabled, .btn-completado:disabled {{ opacity: 0.6; cursor: not-allowed; transform: none; }}
            .resultado-box {{
                margin-top: 20px;
                padding: 15px;
                border-radius: 10px;
                display: none;
            }}
            .resultado-success {{
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            .resultado-warning {{
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeeba;
            }}
            .resultado-info {{
                background: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }}
            .loading-spinner {{
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid rgba(255,255,255,0.3);
                border-radius: 50%;
                border-top-color: white;
                animation: spin 0.8s linear infinite;
                margin-right: 8px;
                vertical-align: middle;
            }}
            @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
            .tiempo-restante {{
                font-size: 14px;
                color: #666;
                margin-top: 10px;
            }}
            hr {{
                margin: 20px 0;
                border: none;
                border-top: 1px solid #e0e0e0;
            }}
            .badge {{
                display: inline-block;
                background: #ffc107;
                color: #856404;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 12px;
                margin-bottom: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="badge">💰 MODO DESARROLLO - PAGO SIMULADO</div>
            <h1>💰 Sección de Pago</h1>
            <p>Dominio verificado correctamente ✅</p>
            
            <div class="monto">$50 USD</div>
            
            <div class="codigo">
                <strong>Código de referencia:</strong><br>
                {codigo}
            </div>
            
            <h3>Datos para transferencia</h3>
            <p>
                Banco: [TU BANCO]<br>
                Cuenta: [TU CUENTA]<br>
                Titular: [TU NOMBRE]<br>
                Concepto: <strong>{codigo}</strong>
            </p>
            
            <hr>
            
            <h3>Opciones de pago</h3>
            <div class="button-group">
                <button onclick="realizarPago()" id="btnPagar" class="btn-pagar">
                    💳 Realizar Pago
                </button>
                <button onclick="simularPagoCompletado()" id="btnCompletado" class="btn-completado">
                    ✅ Pago Completado
                </button>
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
                const resultadoDiv = document.getElementById('resultado');
                resultadoDiv.style.display = 'block';
                resultadoDiv.className = 'resultado-box resultado-' + tipo;
                resultadoDiv.innerHTML = mensaje;
            }}
            
            function limpiarTemporizador() {{
                if (intervalId) {{
                    clearInterval(intervalId);
                    intervalId = null;
                }}
                temporizadorActivo = false;
            }}
            
            async function realizarPago() {{
                const btnPagar = document.getElementById('btnPagar');
                const btnCompletado = document.getElementById('btnCompletado');
                
                btnPagar.disabled = true;
                btnPagar.innerHTML = '<span class="loading-spinner"></span> Redirigiendo a pasarela de pago...';
                
                // Simular redirección a pasarela de pago
                mostrarResultado('info', '🔄 Redirigiendo a la pasarela de pago... (Modo desarrollo - API de pago no integrada aún)');
                
                setTimeout(() => {{
                    mostrarResultado('info', `
                        <strong>💰 EN DESARROLLO</strong><br><br>
                        La integración con pasarelas de pago (Stripe, MercadoPago, PayPal) está en fase beta.<br><br>
                        Por ahora, usa el botón <strong>"Pago Completado"</strong> para simular el proceso.<br><br>
                        <strong>Para producción se integrará:</strong><br>
                        • Stripe - Tarjetas de crédito/débito<br>
                        • PayPal - Cuentas PayPal<br>
                        • Transferencia bancaria (actual)
                    `);
                    btnPagar.disabled = false;
                    btnPagar.innerHTML = '💳 Realizar Pago';
                }}, 2000);
            }}
            
            async function simularPagoCompletado() {{
                if (temporizadorActivo) {{
                    mostrarResultado('warning', '⚠️ Ya hay una simulación de pago en proceso. Espera a que termine.');
                    return;
                }}
                
                const btnCompletado = document.getElementById('btnCompletado');
                const btnPagar = document.getElementById('btnPagar');
                
                // Simular espera de 2 segundos (en producción serán 5 minutos)
                tiempoRestante = 2;
                temporizadorActivo = true;
                
                btnCompletado.disabled = true;
                btnPagar.disabled = true;
                
                mostrarResultado('info', `
                    <strong>🔄 Verificando pago...</strong><br><br>
                    Simulando confirmación de pago...<br>
                    ⏱️ Tiempo restante: <span id="contador">2</span> segundos
                `);
                
                // Actualizar contador cada segundo
                intervalId = setInterval(() => {{
                    tiempoRestante--;
                    const contadorSpan = document.getElementById('contador');
                    if (contadorSpan) {{
                        contadorSpan.textContent = tiempoRestante;
                    }}
                    
                    if (tiempoRestante <= 0) {{
                        clearInterval(intervalId);
                        intervalId = null;
                        
                        // Finalizar simulación y enviar notificación
                        finalizarPagoConfirmado();
                    }}
                }}, 1000);
            }}
            
            async function finalizarPagoConfirmado() {{
                const resultadoDiv = document.getElementById('resultado');
                const btnCompletado = document.getElementById('btnCompletado');
                const btnPagar = document.getElementById('btnPagar');
                
                // Mostrar mensaje de procesando notificación
                resultadoDiv.className = 'resultado-box resultado-info';
                resultadoDiv.innerHTML = '<span class="loading-spinner"></span> Enviando notificación de pago...';
                
                try {{
                    // Enviar notificación al webhook
                    const response = await fetch('/webhook-pago', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ codigo: codigo }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.exitoso) {{
                        mostrarResultado('success', `
                            <strong>✅ ¡PAGO CONFIRMADO!</strong><br><br>
                            ${data.mensaje}<br><br>
                            📧 Se ha enviado una notificación al administrador.<br>
                            📱 Recibirás confirmación por email y WhatsApp.<br><br>
                            <strong>Gracias por confiar en klbrs.es</strong>
                        `);
                        
                        // Deshabilitar botones permanentemente
                        btnCompletado.disabled = true;
                        btnPagar.disabled = true;
                        btnCompletado.style.opacity = '0.5';
                        btnPagar.style.opacity = '0.5';
                        
                        // Mostrar confeti o celebración visual
                        mostrarCelebracion();
                    }} else {{
                        mostrarResultado('warning', `
                            <strong>⚠️ Error en la notificación</strong><br><br>
                            ${data.mensaje}<br><br>
                            Por favor, contacta con soporte.
                        `);
                        btnCompletado.disabled = false;
                        btnPagar.disabled = false;
                    }}
                }} catch (error) {{
                    mostrarResultado('warning', `
                        <strong>⚠️ Error de conexión</strong><br><br>
                        No se pudo enviar la notificación de pago.<br>
                        Intenta nuevamente.
                    `);
                    btnCompletado.disabled = false;
                    btnPagar.disabled = false;
                }} finally {{
                    temporizadorActivo = false;
                    if (intervalId) clearInterval(intervalId);
                    intervalId = null;
                }}
            }}
            
            function mostrarCelebracion() {{
                // Efecto visual simple de celebración
                const colores = ['#28a745', '#20c997', '#17a2b8', '#ffc107'];
                for (let i = 0; i < 20; i++) {{
                    setTimeout(() => {{
                        const div = document.createElement('div');
                        div.style.position = 'fixed';
                        div.style.width = '10px';
                        div.style.height = '10px';
                        div.style.backgroundColor = colores[Math.floor(Math.random() * colores.length)];
                        div.style.borderRadius = '50%';
                        div.style.left = Math.random() * window.innerWidth + 'px';
                        div.style.top = '-10px';
                        div.style.pointerEvents = 'none';
                        div.style.zIndex = '9999';
                        div.style.transition = 'all 1s ease-out';
                        document.body.appendChild(div);
                        
                        setTimeout(() => {{
                            div.style.top = window.innerHeight + 'px';
                            div.style.opacity = '0';
                        }}, 10);
                        
                        setTimeout(() => {{
                            div.remove();
                        }}, 1100);
                    }}, i * 50);
                }}
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
    
    # Verificar si ya estaba pagado
    if usuario_encontrado.get("pagado", False):
        return {"exitoso": True, "mensaje": "Este pago ya había sido confirmado anteriormente"}
    
    # Marcar como pagado
    pendientes[email_encontrado]["pagado"] = True
    pendientes[email_encontrado]["fecha_pago"] = datetime.now().isoformat()
    
    with open(ARCHIVO_PENDIENTES, "w") as f:
        json.dump(pendientes, f, indent=2, ensure_ascii=False)
    
    # Guardar en archivo de pagos
    with open("pagos_registrados.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {email_encontrado} | {usuario_encontrado['nombre']} | {usuario_encontrado['apellido']} | CODIGO: {codigo} | MONTO: ${monto}\n")
    
    logger.info(f"💰 Pago registrado: {email_encontrado} - ${monto}")
    
    # Aquí puedes agregar notificaciones por WhatsApp o Telegram
    # enviar_notificacion_whatsapp(usuario_encontrado, codigo, monto)
    # enviar_notificacion_telegram(usuario_encontrado, codigo, monto)
    
    return {
        "exitoso": True, 
        "mensaje": f"Pago confirmado correctamente. Monto: ${monto}. Recibirás confirmación en tu email."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
