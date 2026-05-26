from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import FileResponse
from app.config import DIRECTORIO_REPORTES
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
        # Ejecutar ZAP y capturar salida
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
            timeout=300
        )
        
        output_text = result.stdout
        logger.info(f"[BG] Código retorno: {result.returncode}")
        logger.info(f"[BG] Longitud salida: {len(output_text)} caracteres")
        
        # Extraer vulnerabilidades usando múltiples patrones
        alertas = []
        
        # Patrón 1: WARN-NEW con formato completo
        patron1 = r'WARN-NEW:\s+([^[]+)\[(\d+)\]\s+x\s+(\d+)'
        matches1 = re.findall(patron1, output_text)
        
        for nombre, vuln_id, ocurrencias in matches1:
            nombre = nombre.strip()
            # Clasificar riesgo
            riesgo = "1"
            if any(x in nombre for x in ["CSP", "Security", "Strict-Transport", "Permissions", "Cross-Origin", "Embedder", "X-Content-Type"]):
                riesgo = "2"
            alertas.append({
                "alert": nombre,
                "riskcode": riesgo,
                "id": vuln_id,
                "instances": int(ocurrencias)
            })
        
        # Patrón 2: WARN-NEW simple (sin ocurrencias)
        if not alertas:
            lineas_warn = [line for line in output_text.split('\n') if 'WARN-NEW:' in line and not line.startswith('WARN-NEW: 0')]
            for linea in lineas_warn:
                # Extraer el nombre
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
        
        # Patrón 3: Buscar líneas que contengan vulnerabilidades conocidas
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
        
        # Si aún no hay alertas pero hay WARN-NEW en la salida, extraer todo
        if not alertas and 'WARN-NEW:' in output_text:
            # Guardar la salida completa para depuración
            debug_path = os.path.join(ruta_absoluta, f"{nombre_base}_debug.txt")
            with open(debug_path, 'w') as f:
                f.write(output_text)
            logger.info(f"[BG] Salida guardada en {debug_path}")
            
            # Extraer líneas WARN-NEW
            for linea in output_text.split('\n'):
                if 'WARN-NEW:' in linea and 'PASS:' not in linea:
                    # Limpiar la línea
                    linea_limpia = linea.replace('WARN-NEW:', '').strip()
                    if linea_limpia and not linea_limpia.startswith('0'):
                        alertas.append({
                            "alert": linea_limpia[:100],  # Primeros 100 caracteres
                            "riskcode": "1",
                            "id": "0",
                            "instances": 1
                        })
        
        logger.info(f"[BG] Alertas encontradas: {len(alertas)}")
        
        # Guardar JSON
        json_path = os.path.join(ruta_absoluta, f"{nombre_base}.json")
        datos_json = {
            "site": [{
                "name": dominio,
                "alerts": alertas,
                "scan_date": datetime.now().isoformat()
            }]
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(datos_json, f, indent=2, ensure_ascii=False)
        
        # Generar HTML
        criticas = sum(1 for a in alertas if a.get('riskcode') == '3')
        medias = sum(1 for a in alertas if a.get('riskcode') == '2')
        bajas = sum(1 for a in alertas if a.get('riskcode') == '1')
        
        html_path = os.path.join(ruta_absoluta, f"{nombre_base}.html")
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reporte Seguridad - {dominio}</title>
    <style>
        body {{ font-family: Arial; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; padding: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .card {{ flex: 1; padding: 20px; border-radius: 8px; text-align: center; color: white; }}
        .card.critical {{ background: #f44336; }}
        .card.medium {{ background: #ff9800; }}
        .card.low {{ background: #4caf50; }}
        .card.total {{ background: #2196f3; }}
        .number {{ font-size: 2em; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Reporte de Seguridad - {dominio}</h1>
        <p>Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <div class="summary">
            <div class="card critical"><div class="number">{criticas}</div>Críticas</div>
            <div class="card medium"><div class="number">{medias}</div>Medias</div>
            <div class="card low"><div class="number">{bajas}</div>Bajas</div>
            <div class="card total"><div class="number">{len(alertas)}</div>Total</div>
        </div>
        <h2>Vulnerabilidades Detectadas</h2>
        <table>
            <tr><th>#</th><th>Vulnerabilidad</th><th>Riesgo</th></tr>"""
        
        for i, a in enumerate(alertas, 1):
            riesgo_text = "Media" if a['riskcode'] == '2' else "Baja"
            html_content += f"<tr><td>{i}</td><td>{a['alert']}</td><td>{riesgo_text}</td></tr>"
        
        html_content += "</table></div></body></html>"
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.info(f"[BG] ✅ Reportes guardados: {len(alertas)} vulnerabilidades")
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
    
    if not email or not dominio:
        return {"exitoso": False, "error": "Email y dominio requeridos"}
    
    logger.info(f"📡 Escaneo solicitado: {email} - {dominio}")
    
    dominio_email = email.split('@')[1]
    nombre_base = f"reporte_{dominio_email}"
    json_path = os.path.join(DIRECTORIO_REPORTES, f"{nombre_base}.json")
    
    # Verificar caché
    if os.path.exists(json_path):
        try:
            cache_age = datetime.now().timestamp() - os.path.getmtime(json_path)
            if cache_age < 3600:
                with open(json_path, "r") as f:
                    datos = json.load(f)
                alertas = datos.get("site", [{}])[0].get("alerts", [])
                logger.info(f"✅ Usando caché: {len(alertas)} alertas")
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
                    "cache": True
                }
        except Exception as e:
            logger.error(f"Error caché: {e}")
    
    # Iniciar escaneo en segundo plano
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
            "url_completa": f"/descargar/reporte_{dominio_email}.html"
        }
    
    return {"completado": False}


@router.get("/descargar/{archivo}")
async def descargar_reporte(archivo: str):
    archivo_path = os.path.join(DIRECTORIO_REPORTES, archivo)
    if not os.path.exists(archivo_path):
        return {"error": "Reporte no encontrado"}
    return FileResponse(path=archivo_path, filename=archivo, media_type="text/html")
