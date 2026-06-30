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

# ============================================
# FUNCIONES PARA PAGOS (AGREGADAS)
# ============================================

def obtener_usuario_por_codigo(codigo: str):
    """
    Obtiene un usuario por su código de verificación
    """
    try:
        import sqlite3
        import os
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "verificaciones.db")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT email, nombre, apellido, codigo, verificado, pagado 
            FROM usuarios 
            WHERE codigo = ?
        """, (codigo,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "email": row[0],
                "nombre": row[1],
                "apellido": row[2],
                "codigo": row[3],
                "verificado": bool(row[4]),
                "pagado": bool(row[5])
            }
        return None
        
    except Exception as e:
        print(f"Error obteniendo usuario por código: {e}")
        return None

def marcar_pagado(email: str):
    """
    Marca un usuario como pagado en la base de datos
    """
    try:
        import sqlite3
        import os
        from datetime import datetime
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "verificaciones.db")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE usuarios 
            SET pagado = 1, fecha_pago = ? 
            WHERE email = ?
        """, (datetime.now().isoformat(), email))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error marcando como pagado: {e}")
        return False

# ============================================
# FUNCIONES PARA PAGOS (AGREGADAS)
# ============================================

def obtener_usuario_por_codigo(codigo: str):
    """
    Obtiene un usuario por su código de verificación
    """
    try:
        import sqlite3
        import os
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "verificaciones.db")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT email, nombre, apellido, codigo, verificado, pagado 
            FROM usuarios 
            WHERE codigo = ?
        """, (codigo,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "email": row[0],
                "nombre": row[1],
                "apellido": row[2],
                "codigo": row[3],
                "verificado": bool(row[4]),
                "pagado": bool(row[5])
            }
        return None
        
    except Exception as e:
        print(f"Error obteniendo usuario por código: {e}")
        return None

def marcar_pagado(email: str):
    """
    Marca un usuario como pagado en la base de datos
    """
    try:
        import sqlite3
        import os
        from datetime import datetime
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "verificaciones.db")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE usuarios 
            SET pagado = 1, fecha_pago = ? 
            WHERE email = ?
        """, (datetime.now().isoformat(), email))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error marcando como pagado: {e}")
        return False
