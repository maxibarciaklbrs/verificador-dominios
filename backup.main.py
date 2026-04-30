from fastapi import FastAPI, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configuración SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "reseller2.networksclub.net")
#SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
MI_EMAIL = os.getenv("MI_EMAIL", SMTP_USER)

# ============================================
# FILTRO DE EMAILS GRATUITOS
# ============================================




### Hasta aca la vdalidacion de dominios gratuitos


def enviar_email(nombre: str, apellido: str, email_usuario: str):
    """
    Envía un email con los datos del formulario
    """
    try:
        msg = EmailMessage()
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = MI_EMAIL
        msg['Subject'] = f"Nuevo registro: {nombre} {apellido}"
        
        contenido = f"""
NUEVO REGISTRO WEB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Nombre completo: {nombre} {apellido}
• Email: {email_usuario}
• Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        msg.set_content(contenido)
        
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email enviado desde {SMTP_FROM_EMAIL} hacia {MI_EMAIL}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("Error de autenticación SMTP")
        return False
    except Exception as e:
        logger.error(f"Error enviando email: {str(e)}")
        return False

# HTML del formulario
html_formulario = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registro</title>
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
    </style>
</head>
<body>
    <div class="form-container">
        <h1>📝 Registro de Usuario</h1>
        <p class="subtitle">Completa tus datos</p>
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
                <label for="email">Email <span class="required">*</span></label>
                <input type="email" id="email" name="email" required placeholder="tu@email.com">
            </div>
            <button type="submit">Enviar ✨</button>
        </form>
        <div id="loading" class="loading">Enviando, por favor espera...</div>
    </div>
    <script>
        document.getElementById('registroForm').addEventListener('submit', function() {
            document.getElementById('loading').style.display = 'block';
            document.querySelector('button').disabled = true;
        });
    </script>
</body>
</html>
"""

# HTML de confirmación (con llaves dobles para CSS)
html_confirmacion = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registro Exitoso</title>
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
            max-width: 450px;
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
        }}
        .user-data {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: left;
        }}
        .user-data strong {{
            color: #667eea;
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
        <div class="success-icon">✓</div>
        <h1>¡Registro Exitoso!</h1>
        <p>Gracias por registrarte</p>
        <div class="user-data">
            <strong>📋 Datos enviados:</strong><br><br>
            <strong>Nombre:</strong> {nombre} {apellido}<br>
            <strong>Email:</strong> {email}
        </div>
        <p>📧 Hemos recibido tus datos correctamente.</p>
        <a href="/" class="btn-back">← Volver</a>
    </div>
</body>
</html>
"""

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
    background_tasks.add_task(enviar_email, nombre, apellido, email)
    
    with open("registros.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp} | {nombre} {apellido} | {email}\n")
    
    return html_confirmacion.format(
        nombre=nombre,
        apellido=apellido,
        email=email
    )
