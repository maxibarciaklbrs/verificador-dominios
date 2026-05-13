# utils.py
import re
import secrets
import string
from datetime import datetime, timedelta
import json
import os
import subprocess
from config import ARCHIVO_PENDIENTES

def email_es_corporativo(email: str):
    if '@' not in email:
        return False, "Email inválido"
    dominios_gratuitos = [
        'gmail.com', 'googlemail.com', 'hotmail.com', 'outlook.com',
        'live.com', 'msn.com', 'yahoo.com', 'ymail.com', 'rocketmail.com',
        'protonmail.com', 'proton.me', 'mail.com', 'gmx.com', 'aol.com',
        'icloud.com', 'me.com', 'mac.com', 'yandex.com', 'mailinator.com'
    ]
    dominio = email.split('@')[1].lower()
    if dominio in dominios_gratuitos:
        return False, f"No se permiten emails de {dominio}. Usa un email corporativo."
    return True, "Email corporativo válido"

def limpiar_dominio(dominio: str) -> str:
    dominio = re.sub(r'^https?://', '', dominio)
    dominio = dominio.split('/')[0]
    return dominio.lower().strip()

def verificar_dns_txt(dominio: str, codigo: str) -> dict:
    resultado = {"existe": False, "detalle": "", "registros": []}
    dominio = limpiar_dominio(dominio)
    try:
        proceso = subprocess.run(
            ['dig', dominio, 'TXT', '+short'],
            capture_output=True,
            text=True,
            timeout=15
        )
        if proceso.returncode == 0 and proceso.stdout:
            for linea in proceso.stdout.strip().split('\n'):
                txt_value = linea.strip('"')
                resultado["registros"].append(txt_value)
                if codigo in txt_value:
                    resultado["existe"] = True
                    resultado["detalle"] = "Código encontrado en registro TXT"
                    return resultado
            resultado["detalle"] = "Código NO encontrado en ningún registro TXT"
        else:
            resultado["detalle"] = f"No hay registros TXT en {dominio}"
    except subprocess.TimeoutExpired:
        resultado["detalle"] = "Timeout - El comando dig no respondió"
    except FileNotFoundError:
        resultado["detalle"] = "Comando 'dig' no instalado"
    except Exception as e:
        resultado["detalle"] = f"Error: {str(e)}"
    return resultado

def generar_codigo_verificacion(longitud: int = 43) -> str:
    caracteres = string.ascii_letters + string.digits + "-_"
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

def guardar_o_obtener_codigo(email: str, nombre: str, apellido: str):
    pendientes = {}
    if os.path.exists(ARCHIVO_PENDIENTES):
        with open(ARCHIVO_PENDIENTES, "r", encoding="utf-8") as f:
            pendientes = json.load(f)
    if email in pendientes:
        return pendientes[email]["codigo"], False
    codigo = generar_codigo_verificacion()
    pendientes[email] = {
        "codigo": codigo,
        "nombre": nombre,
        "apellido": apellido,
        "dominio": email.split('@')[1],
        "fecha_registro": datetime.now().isoformat(),
        "fecha_expiracion": (datetime.now() + timedelta(days=7)).isoformat(),
        "verificado": False,
        "pagado": False
    }
    with open(ARCHIVO_PENDIENTES, "w", encoding="utf-8") as f:
        json.dump(pendientes, f, indent=2, ensure_ascii=False)
    return codigo, True

def extraer_resumen(datos_zap: dict) -> dict:
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
