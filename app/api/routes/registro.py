from fastapi import (
    APIRouter,
    Form,
    BackgroundTasks,
    Request
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.validations.validations import (
    normalize_name,
    normalize_email,
    normalize_phone,
    validate_name,
    validate_email_format,
    validate_email_corporate,
    validate_phone
)

from app.services.email_service import (
    enviar_email_verificacion,
    enviar_email_admin
)

from app.models import guardar_o_obtener_codigo

from datetime import datetime
import logging
import httpx

router = APIRouter()
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")

# ==========================================================
# GET FORM
# ==========================================================

@router.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse(
        "formulario.html",
        {"request": request}
    )

# ==========================================================
# TURNSTILE
# ==========================================================

TURNSTILE_SECRET = "0x4AAAAAADeKap4zAyPENr_eDwCCf84T8os"


async def verify_turnstile(token: str, ip: str):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": TURNSTILE_SECRET,
                "response": token,
                "remoteip": ip
            }
        )
        return r.json()


# ==========================================================
# ERROR HTML
# ==========================================================

def error_html(msg: str):
    return f"""
    <html>
        <head>
            <link rel="stylesheet" href="/static/css/style.css">
        </head>
        <body style="
            text-align:center;
            background-image: url('/static/assets/images/oficinas_klbrs.png');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            min-height: 100vh;
        ">  
        
            <div style="
                background: white;
                padding: 3em;
                max-width: 600px;
                margin: 5em auto;
                border-radius: 10px;
                text-align: center;
            ">
                <h1>{msg}</h1>
                <a class="button" href="/">← Volver al inicio</a>
            </div>     
                    </body>
                </html>
                """


# ==========================================================
# SUBMIT FORM
# ==========================================================

@router.post("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    background_tasks: BackgroundTasks,
    nombre: str = Form(...),
    apellido: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(None),
    turnstile_token: str = Form(...)
):

    # --------------------------
    # NORMALIZACIÓN
    # --------------------------
    nombre = normalize_name(nombre)
    apellido = normalize_name(apellido)
    email = normalize_email(email)
    if telefono:
        telefono = normalize_phone(telefono)

    # --------------------------
    # VALIDACIONES
    # --------------------------
    if not validate_name(nombre):
        return error_html("Nombre inválido")

    if not validate_name(apellido):
        return error_html("Apellidos inválidos")

    if not validate_email_format(email):
        return error_html("Email inválido")

    if not validate_email_corporate(email):
        return error_html("Email no corporativo")

    if not validate_phone(telefono):
        return error_html("Teléfono inválido")

    # --------------------------
    # TURNSTILE
    # --------------------------
    result = await verify_turnstile(
        turnstile_token,
        request.client.host
    )

    if not result.get("success"):
        return error_html("Error de verificación CAPTCHA")

    # --------------------------
    # SQLITE / DB LAYER
    # --------------------------
    try:
        codigo_verificacion, es_nuevo = guardar_o_obtener_codigo(
            email=email,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono 
        )
    except Exception as e:
        logger.error(f"Error SQLite: {e}")
        return error_html("Error interno del servidor")

    # --------------------------
    # EMAILS ASÍNCRONOS
    # --------------------------
    background_tasks.add_task(
        enviar_email_verificacion,
        nombre,
        apellido,
        email,
        codigo_verificacion
    )

    if es_nuevo:
        background_tasks.add_task(
            enviar_email_admin,
            nombre,
            apellido,
            email,
            codigo_verificacion,
            True
        )

    # --------------------------
    # LOG AUDITORÍA
    # --------------------------
    try:
        with open("registros.txt", "a", encoding="utf-8") as f:
            f.write(
                f"{datetime.now()} | {nombre} {apellido} | {email} | {telefono} | CODIGO: {codigo_verificacion} | {'NUEVO' if es_nuevo else 'REUTILIZADO'}\n"
            )
    except Exception as e:
        logger.warning(f"Error escribiendo log: {e}")

    # --------------------------
    # RESPUESTA
    # --------------------------
    return templates.TemplateResponse(
    "registro-confirmacion.html",
    {
        "request": request,
        "nombre": nombre,
        "apellido": apellido,
        "email": email,
        "telefono": telefono,
        "codigo": codigo_verificacion,
        "dominio": email.split("@")[1],
        "ya_existia": not es_nuevo
    }
)