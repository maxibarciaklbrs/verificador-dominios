from fastapi import APIRouter, Form, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from app.services import email_es_corporativo
from app.services.email_service import enviar_email_verificacion, enviar_email_admin
from app.models import guardar_o_obtener_codigo
from app.services.html_service import generar_html_confirmacion
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# HTML del formulario (se mantiene igual)
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


@router.get("/", response_class=HTMLResponse)
async def get_form():
    return html_formulario


@router.post("/submit", response_class=HTMLResponse)
async def submit_form(
    background_tasks: BackgroundTasks,
    nombre: str = Form(...),
    apellido: str = Form(...),
    email: str = Form(...)
):
    es_valido, mensaje = email_es_corporativo(email)
    
    if not es_valido:
        return f"""<html><body style="font-family:sans-serif;padding:40px;text-align:center;"><h1>⛔ {mensaje}</h1><a href="/">Volver</a></body></html>"""
    
    # Usa SQLite en lugar de JSON
    codigo_verificacion, es_nuevo = guardar_o_obtener_codigo(email, nombre, apellido)
    
    background_tasks.add_task(enviar_email_verificacion, nombre, apellido, email, codigo_verificacion)
    
    if es_nuevo:
        background_tasks.add_task(enviar_email_admin, nombre, apellido, email, codigo_verificacion, True)
    
    # Guardar en archivo de log (opcional, solo para auditoría)
    with open("registros.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | {nombre} {apellido} | {email} | CODIGO: {codigo_verificacion} | {'NUEVO' if es_nuevo else 'REUTILIZADO'}\n")
    
    return generar_html_confirmacion(nombre, apellido, email, codigo_verificacion, es_nuevo)
