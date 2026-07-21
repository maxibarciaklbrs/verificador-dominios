from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import FileResponse
from app.config import DIRECTORIO_REPORTES
from app.services.burp_service import burp_habilitado, escanear_sincrono as escanear_burp
from app.services.report_merger import unificar_alertas, generar_reporte_unificado
import os
import json
import subprocess
import logging
import re
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


def ejecutar_escaneo_sync(email: str, dominio: str):
    """Ejecuta escaneo de forma síncrona (en segundo plano)"""
    dominio_email = email.split('@')[1]
    nombre_base = f"reporte_{dominio_email}"
    ruta_absoluta = os.path.abspath(DIRECTORIO_REPORTES)
    os.makedirs(ruta_absoluta, exist_ok=True)
    
    logger.info(f"🚀 [BG] Iniciando escaneo para {dominio}")
    
    try:
        output_text = ""
        try:
            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    "-v", f"{ruta_absoluta}:/zap/wrk",
                    "ghcr.io/zaproxy/zaproxy:stable",
                    "zap-baseline.py",
                    "-t", f"https://{dominio}"
                ],
                capture_output=True,
                text=True,
                timeout=600
            )
            output_text = result.stdout
            logger.info(f"[BG] Código retorno: {result.returncode}")
            logger.info(f"[BG] Longitud salida: {len(output_text)} caracteres")
        except subprocess.TimeoutExpired as e:
            output_text = (e.stdout or "") if isinstance(e.stdout, str) else ""
            logger.error(f"[BG] ⏱️ ZAP superó el timeout de 600s para {dominio}, se genera reporte con lo que haya salido hasta el corte")
        
        alertas = []
        
        patron1 = r'WARN-NEW:\s+([^[]+)\[(\d+)\]\s+x\s+(\d+)'
        matches1 = re.findall(patron1, output_text)
        
        for nombre, vuln_id, ocurrencias in matches1:
            nombre = nombre.strip()
            riesgo = "1"
            if any(x in nombre for x in ["CSP", "Security", "Strict-Transport", "Permissions", "Cross-Origin", "Embedder", "X-Content-Type"]):
                riesgo = "2"
            alertas.append({
                "alert": nombre,
                "riskcode": riesgo,
                "id": vuln_id,
                "instances": int(ocurrencias)
            })
        
        if not alertas:
            lineas_warn = [line for line in output_text.split('\n') if 'WARN-NEW:' in line and not line.startswith('WARN-NEW: 0')]
            for linea in lineas_warn:
                match = re.search(r'WARN-NEW:\s+([^[]+?)(?:\s*\[|$)', linea)
                if match:
                    nombre = match.group(1).strip()
                    if nombre and len(nombre) > 3:
                        alertas.append({
                            "alert": nombre,
                            "riskcode": "1",
                            "id": "0",
                            "instances": 1
                        })
        
        if not alertas:
            vulnerabilidades_conocidas = [
                "Content Security Policy", "CSP Header", "Strict-Transport-Security",
                "X-Content-Type-Options", "Cross-Origin-Embedder-Policy",
                "Sub Resource Integrity", "Permissions Policy", "Information Disclosure"
            ]
            for linea in output_text.split('\n'):
                for vuln in vulnerabilidades_conocidas:
                    if vuln.lower() in linea.lower() and 'WARN-NEW:' in linea:
                        alertas.append({
                            "alert": vuln,
                            "riskcode": "2" if "CSP" in vuln or "Security" in vuln else "1",
                            "id": "0",
                            "instances": 1
                        })
                        break
        
        if not alertas and 'WARN-NEW:' in output_text:
            debug_path = os.path.join(ruta_absoluta, f"{nombre_base}_debug.txt")
            with open(debug_path, 'w') as f:
                f.write(output_text)
            logger.info(f"[BG] Salida guardada en {debug_path}")
            
            for linea in output_text.split('\n'):
                if 'WARN-NEW:' in linea and 'PASS:' not in linea:
                    linea_limpia = linea.replace('WARN-NEW:', '').strip()
                    if linea_limpia and not linea_limpia.startswith('0'):
                        alertas.append({
                            "alert": linea_limpia[:100],
                            "riskcode": "1",
                            "id": "0",
                            "instances": 1
                        })
        
        logger.info(f"[BG] Alertas ZAP encontradas: {len(alertas)}")

        generar_reporte_unificado(
            dominio,
            [{**a, "fuente": "OWASP ZAP"} for a in alertas],
            ruta_absoluta,
            f"{nombre_base}_zap"
        )

        alertas_burp = []
        if burp_habilitado():
            logger.info(f"[BG] 🟠 Burp Suite habilitado, escaneando {dominio}...")
            resultado_burp = escanear_burp(f"https://{dominio}")
            if resultado_burp:
                alertas_burp = resultado_burp
                generar_reporte_unificado(dominio, alertas_burp, ruta_absoluta, f"{nombre_base}_burp")
                logger.info(f"[BG] ✅ Burp completó: {len(alertas_burp)} hallazgos")
            else:
                logger.warning("[BG] ⚠️ Burp no devolvió resultados (revisar configuración BURP_* o el timeout)")

        alertas_finales = unificar_alertas(alertas, alertas_burp)
        json_path, html_path = generar_reporte_unificado(dominio, alertas_finales, ruta_absoluta, nombre_base)

        logger.info(f"[BG] ✅ Reporte final guardado: {len(alertas_finales)} vulnerabilidades ({len(alertas)} ZAP + {len(alertas_burp)} Burp)")
        return True
        
    except Exception as e:
        logger.error(f"[BG] ❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


@router.post("/lanzar-escaneo")
async def lanzar_escaneo(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    email = data.get("email")
    dominio = data.get("dominio")
    forzar = bool(data.get("forzar", False))
    
    if not email or not dominio:
        return {"exitoso": False, "error": "Email y dominio requeridos"}
    
    logger.info(f"📡 Escaneo solicitado: {email} - {dominio}")
    
    dominio_email = email.split('@')[1]
    nombre_base = f"reporte_{dominio_email}"
    json_path = os.path.join(DIRECTORIO_REPORTES, f"{nombre_base}.json")

    if forzar:
        ruta_absoluta = os.path.abspath(DIRECTORIO_REPORTES)
        if os.path.isdir(ruta_absoluta):
            for f in os.listdir(ruta_absoluta):
                if f.startswith(nombre_base):
                    try:
                        os.remove(os.path.join(ruta_absoluta, f))
                        logger.info(f"🗑️ Reporte viejo eliminado: {f}")
                    except OSError as e:
                        logger.warning(f"No se pudo borrar {f}: {e}")

    if not forzar and os.path.exists(json_path):
        try:
            cache_age = datetime.now().timestamp() - os.path.getmtime(json_path)
            if cache_age < 3600:
                with open(json_path, "r") as f:
                    datos = json.load(f)
                alertas = datos.get("site", [{}])[0].get("alerts", [])
                logger.info(f"Usando caché: {len(alertas)} alertas")
                return {
                    "exitoso": True,
                    "completado": True,
                    "resumen": {
                        "total": len(alertas),
                        "criticas": sum(1 for a in alertas if a.get('riskcode') == '3'),
                        "medias": sum(1 for a in alertas if a.get('riskcode') == '2'),
                        "bajas": sum(1 for a in alertas if a.get('riskcode') == '1'),
                        "detalles": [{"nombre": a['alert'][:50], "riesgo": str(a.get('riskcode', '1'))} for a in alertas[:5]]
                    },
                    "url_completa": f"/descargar/{nombre_base}.html",
                    "descargas": {
                        "unificado": f"/descargar/{nombre_base}.html",
                        "zap": f"/descargar/{nombre_base}_zap.html",
                        "burp": f"/descargar/{nombre_base}_burp.html" if os.path.exists(os.path.join(DIRECTORIO_REPORTES, f"{nombre_base}_burp.html")) else None
                    },
                    "cache": True
                }
        except Exception as e:
            logger.error(f"Error caché: {e}")
    
    background_tasks.add_task(ejecutar_escaneo_sync, email, dominio)
    
    return {
        "exitoso": True,
        "completado": False,
        "mensaje": "Escaneo iniciado. Tardará 2-3 minutos.",
        "escaneando": True
    }


@router.post("/estado-escaneo")
async def estado_escaneo(request: Request):
    data = await request.json()
    email = data.get("email")
    
    if not email:
        return {"completado": False}
    
    dominio_email = email.split('@')[1]
    json_path = os.path.join(DIRECTORIO_REPORTES, f"reporte_{dominio_email}.json")
    
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            datos = json.load(f)
        alertas = datos.get("site", [{}])[0].get("alerts", [])
        return {
            "completado": True,
            "resumen": {
                "total": len(alertas),
                "criticas": sum(1 for a in alertas if a.get('riskcode') == '3'),
                "medias": sum(1 for a in alertas if a.get('riskcode') == '2'),
                "bajas": sum(1 for a in alertas if a.get('riskcode') == '1'),
                "detalles": [{"nombre": a['alert'][:50], "riesgo": str(a.get('riskcode', '1'))} for a in alertas[:5]]
            },
            "url_completa": f"/descargar/reporte_{dominio_email}.html",
            "descargas": {
                "unificado": f"/descargar/reporte_{dominio_email}.html",
                "zap": f"/descargar/reporte_{dominio_email}_zap.html",
                "burp": f"/descargar/reporte_{dominio_email}_burp.html" if os.path.exists(os.path.join(DIRECTORIO_REPORTES, f"reporte_{dominio_email}_burp.html")) else None
            }
        }
    
    return {"completado": False}


@router.get("/descargar/{archivo}")
async def descargar_reporte(archivo: str):
    archivo_path = os.path.join(DIRECTORIO_REPORTES, archivo)
    if not os.path.exists(archivo_path):
        return {"error": "Reporte no encontrado"}
    return FileResponse(path=archivo_path, filename=archivo, media_type="text/html")
