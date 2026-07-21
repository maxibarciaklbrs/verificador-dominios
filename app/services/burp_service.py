# app/services/burp_service.py
"""
Cliente para la REST API de Burp Suite Professional (licencia de klbrs).

CONFIGURACIÓN NECESARIA DEL LADO DE BURP (manual, una sola vez):
1. Abrir Burp Suite Professional (headless o con GUI, en el server que
   corresponda).
2. User options -> Misc -> REST API -> tildar "Service running".
3. Elegir puerto (por defecto 1337) e interfaz donde escucha (si Burp
   corre en otra máquina distinta al backend, no dejarlo en loopback).
4. Generar una API key ahí mismo (botón "New").

CONFIGURACIÓN DE ESTE PROYECTO (.env):
    BURP_ENABLED=true
    BURP_API_URL=http://[Aca completar con la IP/host donde corre Burp]:1337
    BURP_API_KEY=[Aca completar con la API key generada en Burp]
    BURP_SCAN_CONFIG=[Aca completar, opcional: nombre de una config de
        escaneo ya guardada dentro de Burp. Si se deja vacío, usa la
        configuración por defecto de Burp]

Mientras BURP_ENABLED no sea "true", este módulo queda inactivo y el
proyecto sigue escaneando solo con ZAP (comportamiento actual sin tocar).

NOTA: el nombre exacto de los campos que devuelve la API de Burp en
GET /v0.1/scan/{task_id} puede variar un poco según la versión instalada.
Este cliente usa .get() en todos lados para no romper si falta algún
campo, pero conviene revisar la primera vez la respuesta real contra
la documentación autogenerada de la API en:
    http://<BURP_API_URL>/<BURP_API_KEY>/v0.1/<BURP_API_KEY>
y ajustar `_normalizar_issue()` si hiciera falta.
"""

import os
import time
import logging
import httpx

logger = logging.getLogger(__name__)


def burp_habilitado() -> bool:
    return os.getenv("BURP_ENABLED", "false").lower() == "true"


def _config():
    base_url = os.getenv("BURP_API_URL", "").rstrip("/")
    api_key = os.getenv("BURP_API_KEY", "")
    scan_config = os.getenv("BURP_SCAN_CONFIG", "")
    return base_url, api_key, scan_config


def _base_path(base_url: str, api_key: str) -> str:
    return f"{base_url}/{api_key}/v0.1"


def iniciar_scan(url_objetivo: str):
    """Lanza un scan en Burp y devuelve el task_id, o None si falla."""
    base_url, api_key, scan_config = _config()
    if not base_url or not api_key or base_url.startswith("[Aca") or api_key.startswith("[Aca"):
        logger.error("❌ Burp: falta configurar BURP_API_URL / BURP_API_KEY en el .env")
        return None

    payload = {"urls": [url_objetivo]}
    if scan_config:
        payload["scan_configurations"] = [
            {"name": scan_config, "type": "NamedConfiguration"}
        ]

    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(f"{_base_path(base_url, api_key)}/scan", json=payload)

        if response.status_code not in (200, 201):
            logger.error(f"❌ Burp: no se pudo iniciar el scan ({response.status_code}): {response.text[:300]}")
            return None

        location = response.headers.get("location", "")
        task_id = location.rstrip("/").split("/")[-1] if location else None

        if not task_id:
            try:
                task_id = str(response.json().get("task_id"))
            except Exception:
                task_id = None

        if task_id:
            logger.info(f"✅ Burp: scan iniciado, task_id={task_id}")
        return task_id

    except Exception as e:
        logger.error(f"❌ Burp: error iniciando scan: {e}")
        return None


def obtener_estado(task_id: str) -> dict:
    """Consulta el estado de un scan. Devuelve {} si falla la consulta."""
    base_url, api_key, _ = _config()
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(f"{_base_path(base_url, api_key)}/scan/{task_id}")
        if response.status_code == 200:
            return response.json()
        logger.error(f"❌ Burp: estado del scan devolvió {response.status_code}")
        return {}
    except Exception as e:
        logger.error(f"❌ Burp: error consultando estado: {e}")
        return {}


def _normalizar_issue(issue: dict) -> dict:
    """Traduce un issue de Burp al mismo formato que usan las alertas de ZAP."""
    severidad = str(issue.get("severity", "")).lower()
    mapa_riesgo = {"high": "3", "medium": "2", "low": "1", "information": "1", "info": "1"}
    return {
        "alert": issue.get("name") or issue.get("issue_name") or "Vulnerabilidad detectada por Burp",
        "riskcode": mapa_riesgo.get(severidad, "1"),
        "id": str(issue.get("type_index", issue.get("issue_type", "0"))),
        "instances": 1,
        "descripcion": issue.get("description", ""),
        "path": issue.get("path", issue.get("origin", "")),
        "fuente": "Burp Suite",
    }


def escanear_sincrono(url_objetivo: str, timeout_segundos: int = 900):
    """
    Lanza el scan y bloquea sondeando hasta que termine o se acabe el tiempo.
    Pensado para llamarse desde el mismo hilo de background que corre ZAP.
    Devuelve la lista de alertas normalizadas, o None si algo falló
    (falta configurar la API, Burp no responde, timeout, etc.).
    """
    if not burp_habilitado():
        return None

    task_id = iniciar_scan(url_objetivo)
    if not task_id:
        return None

    inicio = time.time()
    while time.time() - inicio < timeout_segundos:
        estado = obtener_estado(task_id)
        status = str(estado.get("scan_status", "")).lower()

        if status == "succeeded":
            issues = [
                ev.get("issue", {})
                for ev in estado.get("issue_events", [])
                if ev.get("issue")
            ]
            logger.info(f"✅ Burp: scan {task_id} completado, {len(issues)} hallazgos")
            return [_normalizar_issue(i) for i in issues]

        if status == "failed":
            logger.error(f"❌ Burp: scan {task_id} falló")
            return None

        time.sleep(10)

    logger.error(f"❌ Burp: scan {task_id} no terminó dentro del timeout ({timeout_segundos}s)")
    return None
