# app/services/report_merger.py
"""
Une las alertas de ZAP y de Burp Suite en un único reporte (JSON + HTML).
"""

import json
import os
from datetime import datetime


def unificar_alertas(alertas_zap: list, alertas_burp: list) -> list:
    """Concatena ambas listas, marcando el origen de cada alerta."""
    resultado = []
    for a in alertas_zap:
        a = dict(a)
        a.setdefault("fuente", "OWASP ZAP")
        resultado.append(a)
    for a in alertas_burp or []:
        resultado.append(a)
    return resultado


def generar_reporte_unificado(dominio: str, alertas: list, ruta_directorio: str, nombre_base: str):
    """
    Genera <nombre_base>.json y <nombre_base>.html con las alertas combinadas.
    Devuelve (ruta_json, ruta_html).
    """
    os.makedirs(ruta_directorio, exist_ok=True)

    criticas = sum(1 for a in alertas if a.get("riskcode") == "3")
    medias = sum(1 for a in alertas if a.get("riskcode") == "2")
    bajas = sum(1 for a in alertas if a.get("riskcode") == "1")

    json_path = os.path.join(ruta_directorio, f"{nombre_base}.json")
    datos_json = {
        "site": [{
            "name": dominio,
            "alerts": alertas,
            "scan_date": datetime.now().isoformat(),
            "fuentes": sorted({a.get("fuente", "Desconocido") for a in alertas}),
        }]
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(datos_json, f, indent=2, ensure_ascii=False)

    filas = ""
    for i, a in enumerate(alertas, 1):
        riesgo_text = {"3": "Crítica", "2": "Media", "1": "Baja"}.get(a.get("riskcode", "1"), "Baja")
        filas += (
            f"<tr><td>{i}</td><td>{a.get('alert', '')}</td>"
            f"<td>{riesgo_text}</td><td>{a.get('fuente', '')}</td></tr>"
        )

    html_path = os.path.join(ruta_directorio, f"{nombre_base}.html")
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reporte Unificado de Seguridad - {dominio}</title>
    <style>
        body {{ font-family: Arial; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; padding: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }}
        .card {{ flex: 1; min-width: 120px; padding: 20px; border-radius: 8px; text-align: center; color: white; }}
        .card.critical {{ background: #f44336; }}
        .card.medium {{ background: #ff9800; }}
        .card.low {{ background: #4caf50; }}
        .card.total {{ background: #2196f3; }}
        .number {{ font-size: 2em; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #4CAF50; color: white; }}
        .fuente-tag {{ font-size: 0.85em; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Reporte Unificado de Seguridad - {dominio}</h1>
        <p>Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p class="fuente-tag">Fuentes combinadas: {", ".join(sorted({a.get('fuente', 'Desconocido') for a in alertas})) or "—"}</p>
        <div class="summary">
            <div class="card critical"><div class="number">{criticas}</div>Críticas</div>
            <div class="card medium"><div class="number">{medias}</div>Medias</div>
            <div class="card low"><div class="number">{bajas}</div>Bajas</div>
            <div class="card total"><div class="number">{len(alertas)}</div>Total</div>
        </div>
        <h2>Vulnerabilidades Detectadas</h2>
        <table>
            <tr><th>#</th><th>Vulnerabilidad</th><th>Riesgo</th><th>Fuente</th></tr>
            {filas}
        </table>
    </div>
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return json_path, html_path
