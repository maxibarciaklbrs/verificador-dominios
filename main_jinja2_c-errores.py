from fastapi import FastAPI, Form, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import logging
from datetime import datetime
import json
import asyncio
import subprocess

# Módulos internos
from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    SMTP_FROM_EMAIL, MI_EMAIL,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    ARCHIVO_PENDIENTES, DIRECTORIO_REPORTES
)
from utils import (
    email_es_corporativo,
    verificar_dns_txt,
    guardar_o_obtener_codigo,
    extraer_resumen
)
from notifications import (
    enviar_email_verificacion,
    enviar_email_admin,
    enviar_notificacion_pago_telegram
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Montar archivos estáticos (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar templates
templates = Jinja2Templates(directory="templates")


# ============================================
# ENDPOINTS PRINCIPALES
# ============================================

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("formulario.html", {"request": request})


@app.post("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    background_tasks: BackgroundTasks,
    nombre: str = Form(...),
    apellido: str = Form(...),
    email: str = Form(...)
):
    es_valido, mensaje = email_es_corporativo(email)

    if not es_valido:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "mensaje": mensaje
        })

    codigo_verificacion, es_nuevo = guardar_o_obtener_codigo(email, nombre, apellido)

    background_tasks.add_task(enviar_email_verificacion, nombre, apellido, email, codigo_verificacion)

    if es_nuevo:
        background_tasks.add_task(enviar_email_admin, nombre, apellido, email, codigo_verificacion, True)

    with open("registros.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | {nombre} {apellido} | {email} | CODIGO: {codigo_verificacion} | {'NUEVO' if es_nuevo else 'REUTILIZADO'}\n")

    dominio = email.split('@')[1]
    return templates.TemplateResponse("confirmacion.html", {
        "request": request,
        "nombre": nombre,
        "apellido": apellido,
        "email": email,
        "codigo": codigo_verificacion,
        "dominio": dominio,
        "ya_existia": not es_nuevo   # True si ya existía
    })


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
async def pagina_pago(request: Request, codigo: str):
    return templates.TemplateResponse("pago.html", {
        "request": request,
        "codigo": codigo
    })


# ============================================
# WEBHOOK DE PAGO
# ============================================

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

    if usuario_encontrado.get("pagado", False):
        return {"exitoso": True, "mensaje": "Este pago ya había sido confirmado anteriormente"}

    pendientes[email_encontrado]["pagado"] = True
    pendientes[email_encontrado]["fecha_pago"] = datetime.now().isoformat()

    with open(ARCHIVO_PENDIENTES, "w") as f:
        json.dump(pendientes, f, indent=2, ensure_ascii=False)

    with open("pagos_registrados.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {email_encontrado} | {usuario_encontrado['nombre']} | {usuario_encontrado['apellido']} | CODIGO: {codigo} | MONTO: ${monto}\n")

    logger.info(f"💰 Pago registrado: {email_encontrado} - ${monto}")

    # Notificación Telegram
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
# MOTOR DE ESCANEO ZAP (mantenido igual)
# ============================================

async def ejecutar_escaneo_zap(dominio_objetivo: str, email_usuario: str):
    """Ejecuta ZAP en segundo plano."""
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
        logger.info(f"🚀 Iniciando escaneo ZAP para {dominio_objetivo}")
        proceso = await asyncio.create_subprocess_exec(
            *comando,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proceso.communicate()
        if proceso.returncode != 0:
            logger.error(f"❌ Error en escaneo ZAP: {stderr.decode()}")
            return None
        subprocess.run(["sudo", "chown", "kali:kali", f"{nombre_base}.html", f"{nombre_base}.json"], check=False)
        logger.info(f"✅ Escaneo completado. Reportes: {nombre_base}.html / {nombre_base}.json")
        return nombre_base
    except Exception as e:
        logger.error(f"❌ Error ejecutando escaneo: {e}")
        return None


# ============================================
# ENDPOINTS DE AUDITORÍA
# ============================================

@app.post("/lanzar-escaneo")
async def lanzar_escaneo(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    email = data.get("email")
    dominio = data.get("dominio")
    if not email or not dominio:
        return {"exitoso": False, "error": "Email y dominio requeridos"}
    nombre_base = f"reporte_{email.split('@')[1]}"
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
    background_tasks.add_task(ejecutar_escaneo_zap, dominio, email)
    logger.info(f"🔄 Escaneo lanzado en background para {email}")
    return {
        "exitoso": True,
        "mensaje": "Escaneo iniciado. Durará 2-3 minutos.",
        "escaneando": True
    }


@app.post("/estado-escaneo")
async def estado_escaneo(request: Request):
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
