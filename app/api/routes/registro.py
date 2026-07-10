from fastapi import (
    APIRouter,
    Form,
    BackgroundTasks,
    Request
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.captcha_service import (
    verificar_turnstile
)

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

from app.services.registro_service import registrar_usuario

from app.exceptions.registro_exceptions import (
    RegistroError,
    DominioInvalidoError
)

import logging

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

                <a class="button" href="/">
                    ← Volver al inicio
                </a>

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

    # --------------------------------------------------
    # Normalización
    # --------------------------------------------------

    nombre = normalize_name(nombre)
    apellido = normalize_name(apellido)
    email = normalize_email(email)

    if telefono:
        telefono = normalize_phone(telefono)

    # --------------------------------------------------
    # Validaciones
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Turnstile
    # --------------------------------------------------

    captcha_valido = await verificar_turnstile(turnstile_token,request.client.host)

    if not captcha_valido:
        return error_html("Error de verificación CAPTCHA")

    # --------------------------------------------------
    # Registro
    # --------------------------------------------------

    try:

        resultado = registrar_usuario(
            email=email,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono
        )

        
        dominio = resultado["dominio"]

        codigo_verificacion = dominio["codigo"]
        es_nuevo = resultado["usuario_creado"]

    except DominioInvalidoError as e:

        logger.warning(str(e))
        return error_html(str(e))

    except RegistroError:

        logger.exception("Error durante el registro")
        return error_html("Error interno del servidor.")

    # --------------------------------------------------
    # Emails
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Respuesta
    # --------------------------------------------------

    return templates.TemplateResponse(
        "registro-confirmacion.html",
        {
            "request": request,
            "nombre": nombre,
            "apellido": apellido,
            "email": email,
            "telefono": telefono,
            "codigo": codigo_verificacion,
            "dominio": dominio["nombre"],
            "ya_existia": not es_nuevo
        }
    )