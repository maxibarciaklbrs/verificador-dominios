from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import FileResponse
from app.config import DIRECTORIO_REPORTES
import os
import json
import subprocess
import asyncio
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


async def ejecutar_escaneo_zap(dominio_objetivo: str, email_usuario: str):
    """Ejecuta ZAP en segundo plano"""
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
            logger.error(f"Error en escaneo ZAP: {stderr.decode()}")
            return None
        
        subprocess.run(["sudo", "chown", "kali:kali", f"{nombre_base}.html", f"{nombre_base}.json"], check=False)
        
        logger.info(f"Escaneo completado para {email_usuario}")
        return nombre_base
        
    except Exception as e:
        logger.error(f"Error ejecutando escaneo: {e}")
        return None


def extraer_resumen(datos_zap: dict) -> dict:
    """Extrae resumen del JSON de ZAP"""
    alertas = datos_zap.get("site", [{}])[0].get("alerts", [])
    
    criticas = [a for a in alertas if a.get('riskcode') == '3']
    medias = [a for a in alertas if a.get('riskcode') == '2']
    bajas = [a for a in alertas if a.get('riskcode') == '1']
    
    return {
        "total": len(alertas),
        "criticas": len(criticas),
        "medias": len(medias),
        "bajas": len(bajas),
        "detalles": [{"nombre": a['alert'], "riesgo": a.get('riskcode', '0')} for a in alertas[:5]]
    }


@router.post("/lanzar-escaneo")
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
            return {
                "exitoso": True,
                "resumen": resumen,
                "url_completa": f"/descargar/{nombre_base}.html",
                "cache": True
            }
        except:
            pass
    
    background_tasks.add_task(ejecutar_escaneo_zap, dominio, email)
    
    return {
        "exitoso": True,
        "mensaje": "Escaneo iniciado. Durará 2-3 minutos.",
        "escaneando": True
    }


@router.post("/estado-escaneo")
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


@router.get("/descargar/{archivo}")
async def descargar_reporte(archivo: str):
    if os.path.exists(archivo):
        return FileResponse(path=archivo, filename=archivo, media_type="text/html")
    return {"error": "Reporte no encontrado. Ejecuta primero el escaneo."}
