#!/usr/bin/env python3
"""
Verificador de dominios - DNS TXT o URL
Uso: python verificar.py "CODIGO" "DOMINIO" "METODO"

EJEMPLOS:
    python verificar.py "MiCodigo123" "klbrs.es" "URL"
    python verificar.py "MiCodigo123" "http://klbrs.es" "URL"
    python verificar.py "MiCodigo123" "klbrs.es" "DNS"
    python verificar.py "MiCodigo123" "https://klbrs.es" "DNS"
"""

import sys
import urllib.request
import urllib.error
import ssl
import subprocess
import re

# ============================================
# FUNCIONES DE VERIFICACIÓN
# ============================================

def limpiar_dominio(dominio: str) -> str:
    """
    Extrae solo el nombre del dominio, con o sin http://
    Ejemplos:
        "klbrs.es" -> "klbrs.es"
        "http://klbrs.es" -> "klbrs.es"
        "https://klbrs.es" -> "klbrs.es"
        "http://klbrs.es/ruta" -> "klbrs.es"
    """
    # Eliminar protocolo http:// o https://
    dominio = re.sub(r'^https?://', '', dominio)
    # Eliminar cualquier cosa después de la primera barra
    dominio = dominio.split('/')[0]
    return dominio.lower().strip()

def verificar_url_existe(url: str, timeout: int = 10) -> tuple:
    """Verifica si una URL existe (código 200 OK)"""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as response:
            status = response.getcode()
            if status == 200:
                return (True, status, "✅ URL existe (HTTP 200)")
            else:
                return (False, status, f"❌ URL responde con HTTP {status}")
                
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return (False, e.code, f"❌ URL no encontrada (HTTP 404)")
        elif e.code == 403:
            return (True, e.code, f"✅ URL existe pero acceso denegado (HTTP 403)")
        else:
            return (False, e.code, f"❌ Error HTTP {e.code}")
    except Exception as e:
        return (False, 0, f"❌ Error: {str(e)[:50]}")

def verificar_dns_txt(dominio: str, codigo: str) -> dict:
    """Verifica usando dig y busca el código dentro de los registros"""
    resultado = {
        "metodo": "DNS TXT",
        "dominio": dominio,
        "codigo": codigo,
        "existe": False,
        "detalle": "",
        "registros": []
    }
    
    try:
        print(f"   🔍 Ejecutando: dig {dominio} TXT")
        proceso = subprocess.run(
            ['dig', dominio, 'TXT', '+short'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if proceso.returncode == 0 and proceso.stdout:
            lineas = proceso.stdout.strip().split('\n')
            
            for linea in lineas:
                txt_value = linea.strip('"')
                resultado["registros"].append(txt_value)
                
                # Buscar el código DENTRO del registro
                if codigo in txt_value:
                    resultado["existe"] = True
                    resultado["detalle"] = f"✅ Código encontrado DENTRO del registro TXT"
                    return resultado
            
            resultado["detalle"] = f"❌ Código NO encontrado en ningún registro TXT"
            return resultado
        else:
            resultado["detalle"] = f"❌ No hay registros TXT en {dominio}"
            return resultado
            
    except subprocess.TimeoutExpired:
        resultado["detalle"] = "❌ Timeout - El comando dig no respondió"
        return resultado
    except FileNotFoundError:
        resultado["detalle"] = "❌ Comando 'dig' no instalado. Instala: sudo apt install dnsutils"
        return resultado
    except Exception as e:
        resultado["detalle"] = f"❌ Error: {str(e)}"
        return resultado

def verificar_url(dominio: str, codigo: str) -> dict:
    """Verifica si la URL existe"""
    resultado = {
        "metodo": "URL",
        "dominio": dominio,
        "codigo": codigo,
        "existe": False,
        "detalle": "",
        "url_encontrada": None
    }
    
    urls = [
        f"https://{dominio}/{codigo}.txt",
        f"http://{dominio}/{codigo}.txt",
    ]
    
    for url in urls:
        print(f"   🔍 Verificando: {url}")
        existe, status, mensaje = verificar_url_existe(url)
        
        if existe:
            resultado["existe"] = True
            resultado["detalle"] = f"✅ {mensaje}"
            resultado["url_encontrada"] = url
            return resultado
        else:
            print(f"      {mensaje}")
    
    resultado["detalle"] = f"❌ La URL no existe"
    return resultado

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def main():
    if len(sys.argv) < 4:
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                    VERIFICADOR DE DOMINIOS                        ║
╚══════════════════════════════════════════════════════════════════╝

USO:
    python verificar.py "CODIGO" "DOMINIO" "METODO"

ARGUMENTOS:
    CODIGO   : Código de verificación
    DOMINIO  : Dominio (ej: klbrs.es o http://klbrs.es)
    METODO   : URL o DNS

EJEMPLOS:
    # Con o sin http:// - ambas funcionan:
    python verificar.py "MiCodigo123" "klbrs.es" "URL"
    python verificar.py "MiCodigo123" "http://klbrs.es" "URL"
    python verificar.py "MiCodigo123" "https://klbrs.es" "URL"
    
    # Para DNS también funciona con o sin http://:
    python verificar.py "MiCodigo123" "klbrs.es" "DNS"
    python verificar.py "MiCodigo123" "http://klbrs.es" "DNS"

MÉTODO URL - Verifica si existe:
    https://dominio/CODIGO.txt (HTTP 200)
    
MÉTODO DNS - Verifica si el código está dentro de algún registro TXT
        """)
        sys.exit(1)
    
    codigo = sys.argv[1]
    dominio_raw = sys.argv[2]
    metodo = sys.argv[3].upper().strip()
    
    # Limpiar dominio (extraer solo el nombre, con o sin http://)
    dominio = limpiar_dominio(dominio_raw)
    
    # Validaciones
    if not codigo:
        print("❌ Error: Código vacío")
        sys.exit(1)
    
    if not dominio or '.' not in dominio:
        print(f"❌ Error: Dominio inválido: '{dominio_raw}'")
        print(f"   Ejemplos válidos: klbrs.es, http://klbrs.es, https://klbrs.es")
        sys.exit(1)
    
    if metodo not in ["URL", "DNS"]:
        print("❌ Error: Método inválido. Usa 'URL' o 'DNS'")
        sys.exit(1)
    
    # Mostrar información
    print("\n" + "="*60)
    print("🔍 VERIFICACIÓN DE DOMINIO")
    print("="*60)
    print(f"📝 Código    : {codigo}")
    print(f"🌐 Dominio   : {dominio} (original: {dominio_raw})")
    print(f"🔧 Método    : {metodo}")
    print("="*60)
    
    print("\n🔎 Verificando...\n")
    
    # Ejecutar verificación
    if metodo == "DNS":
        resultado = verificar_dns_txt(dominio, codigo)
    else:
        resultado = verificar_url(dominio, codigo)
    
    # Mostrar resultado
    print(f"\n📡 RESULTADO:")
    print(f"   {resultado['detalle']}")
    
    if resultado.get('url_encontrada'):
        print(f"\n🔗 URL verificada:")
        print(f"   → {resultado['url_encontrada']}")
    
    if resultado.get('registros'):
        print(f"\n📋 Registros TXT encontrados:")
        for r in resultado['registros'][:3]:
            if len(r) > 80:
                r = r[:77] + "..."
            print(f"   → {r}")
    
    print("\n" + "="*60)
    
    if resultado['existe']:
        print("🎉 VERIFICACIÓN EXITOSA - El dominio está verificado")
        sys.exit(0)
    else:
        print("❌ VERIFICACIÓN FALLIDA")
        sys.exit(1)

if __name__ == "__main__":
    main()
