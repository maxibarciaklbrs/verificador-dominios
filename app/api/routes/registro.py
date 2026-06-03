from fastapi import (
    APIRouter,
    Form,
    BackgroundTasks,
    Request
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services import email_es_corporativo
from app.services.email_service import enviar_email_verificacion, enviar_email_admin
from app.models import guardar_o_obtener_codigo
from app.services.html_service import generar_html_confirmacion

from datetime import datetime
import logging, requests

router = APIRouter()
logger = logging.getLogger(__name__)

# Ruta donde están los templates
templates = Jinja2Templates(
    directory="templates"
)

# ==========================================================
# GET /
# Carga formulario.html
# ==========================================================

@router.get(
    "/",
    response_class=HTMLResponse
)
async def get_form(request: Request):

    return templates.TemplateResponse(
        "formulario.html",
        {
            "request": request
        }
    )

# ==========================================================
# Turnstile
# ==========================================================

TURNSTILE_SECRET = "0x4AAAAAADeKap4zAyPENr_eDwCCf84T8os"

def verify_turnstile(token: str, ip: str):
    r = requests.post(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data={
            "secret": TURNSTILE_SECRET,
            "response": token,
            "remoteip": ip
        }
    )
    return r.json()
    
# ==========================================================
# POST /submit
# Procesa formulario
# ==========================================================

@router.post(
    "/submit",
    response_class=HTMLResponse
)

async def submit_form(

    request: Request,
    background_tasks: BackgroundTasks,
    nombre: str = Form(...),
    apellido: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(...),
    turnstile_token: str = Form(...)
):  
    result = verify_turnstile(turnstile_token, request.client.host)

    if not result.get("success"):
        return """
        <html>
        <body style="font-family:sans-serif;padding:40px;text-align:center;">
            <h1>⛔ Error de verificación CAPTCHA</h1>
            <p>Inténtalo de nuevo.</p>
            <a href="/">Volver</a>
        </body>
        </html>
    """
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
        f.write(f"{datetime.now()} | {nombre} {apellido} | {email} | {telefono} | CODIGO: {codigo_verificacion} | {'NUEVO' if es_nuevo else 'REUTILIZADO'}\n")
    
    return generar_html_confirmacion(nombre, apellido, email, telefono, codigo_verificacion, es_nuevo)

