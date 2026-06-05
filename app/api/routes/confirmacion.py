from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from app.services.codigo_service import generar_codigo_verificacion
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.post("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    email: str = Form(...),
    nombre: str = Form(...),
    apellido: str = Form(...),
    telefono: str = Form(...)
):
    codigo = generar_codigo_verificacion()
    dominio = email.split("@")[1]

    return templates.TemplateResponse(
        "registro-confirmacion.html",
        {
            "request": request,
            "email": email,
            "nombre": nombre,
            "apellido": apellido,
            "telefono": telefono,
            "codigo": codigo,
            "dominio": dominio,
            "ya_existia": False
        }
    )