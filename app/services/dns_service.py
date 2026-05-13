import logging
import subprocess
import re
from app.config import DOMINIOS_BLOQUEADOS

logger = logging.getLogger(__name__)

def limpiar_dominio(dominio: str) -> str:
    dominio = re.sub(r'^https?://', '', dominio)
    dominio = dominio.split('/')[0]
    dominio = re.sub(r'^www\.', '', dominio)
    return dominio.lower().strip()

def verificar_dns_txt(dominio: str, codigo: str) -> dict:
    resultado = {"existe": False, "detalle": "", "registros": []}
    dominio = limpiar_dominio(dominio)
    
    try:
        logger.info(f"🔍 Verificando DNS TXT de {dominio}")
        proceso = subprocess.run(
            ['dig', dominio, 'TXT', '+short'],
            capture_output=True, text=True, timeout=15
        )
        
        if proceso.returncode == 0 and proceso.stdout:
            for linea in proceso.stdout.strip().split('\n'):
                txt_value = linea.strip('"')
                resultado["registros"].append(txt_value)
                if codigo in txt_value:
                    resultado["existe"] = True
                    resultado["detalle"] = "✅ Código encontrado"
                    return resultado
            resultado["detalle"] = "❌ Código NO encontrado"
        else:
            resultado["detalle"] = f"ℹ️ No hay registros TXT en {dominio}"
    except subprocess.TimeoutExpired:
        resultado["detalle"] = "⏱️ Timeout"
    except FileNotFoundError:
        resultado["detalle"] = "❌ Comando 'dig' no instalado"
    except Exception as e:
        resultado["detalle"] = f"❌ Error: {str(e)}"
    
    return resultado

def email_es_corporativo(email: str) -> tuple:
    if '@' not in email:
        return False, "Email inválido"
    dominio = email.split('@')[1].lower()
    if dominio in DOMINIOS_BLOQUEADOS:
        return False, f"No se permiten emails de {dominio}"
    return True, "Email corporativo válido"
