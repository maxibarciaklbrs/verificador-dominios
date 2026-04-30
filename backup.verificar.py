#!/usr/bin/env python3
"""
Verificador de dominios - DNS TXT o URL
Uso: python verificar.py "CODIGO" "DOMINIO" "METODO"
"""

import sys
import dns.resolver
import requests
import urllib3
from urllib.parse import urlparse

# Deshabilitar warnings de SSL para pruebas
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================
# FUNCIONES DE VERIFICACIÓN
# ============================================

def limpiar_dominio(dominio: str) -> str:
    """Limpia el dominio eliminando protocolos y rutas"""
    # Eliminar http:// o https://
    dominio = dominio.replace('http://', '').replace('https://', '')
    # Eliminar barra final y cualquier ruta
    dominio = dominio.split('/')[0]
    return dominio.lower().strip()

def verificar_dns_txt(dominio: str, codigo: str) -> dict:
    """Verifica si el código existe en registros TXT del dominio"""
    resultado = {
        "metodo": "DNS TXT",
        "dominio": dominio,
        "codigo": codigo,
        "existe": False,
        "detalle": "",
        "registros": []
    }
    
    try:
        print(f"   🔍 Consultando DNS de {dominio}...")
        respuestas = dns.resolver.resolve(dominio, 'TXT')
        
        for respuesta in respuestas:
            txt_value = str(respuesta).strip('"')
            resultado["registros"].append(txt_value)
            
            if codigo == txt_value:
                resultado["existe"] = True
                resultado["detalle"] = f"✅ Coincidencia EXACTA en registro TXT"
                return resultado
            elif codigo in txt_value:
                resultado["existe"] = True
                resultado["detalle"] = f"✅ Coincidencia PARCIAL en registro TXT"
                return resultado
        
        resultado["detalle"] = f"❌ No se encontró el código en ningún registro TXT"
        return resultado
        
    except dns.resolver.NXDOMAIN:
        resultado["detalle"] = f"❌ El dominio '{dominio}' no existe"
        return resultado
    except dns.resolver.NoAnswer:
        resultado["detalle"] = f"❌ El dominio '{dominio}' no tiene registros TXT"
        return resultado
    except dns.resolver.Timeout:
        resultado["detalle"] = "❌ Timeout - El servidor DNS no respondió"
        return resultado
    except Exception as e:
        resultado["detalle"] = f"❌ Error DNS: {str(e)}"
        return resultado

def verificar_url(dominio: str, codigo: str) -> dict:
    """Verifica si existe un archivo .txt con el código en el dominio"""
    resultado = {
        "metodo": "URL / Archivo TXT",
        "dominio": dominio,
        "codigo": codigo,
        "existe": False,
        "detalle": "",
        "url_encontrada": None
    }
    
    # Posibles rutas donde podría estar el archivo
    rutas = [
        f"https://{dominio}/.well-known/{codigo}.txt",
        f"http://{dominio}/.well-known/{codigo}.txt",
        f"https://{dominio}/{codigo}.txt",
        f"http://{dominio}/{codigo}.txt",
        f"https://{dominio}/.well-known/verificacion/{codigo}.txt",
        f"http://{dominio}/.well-known/verificacion/{codigo}.txt",
    ]
    
    for url in rutas:
        try:
            response = requests.get(url, timeout=10, verify=False)
            
            if response.status_code == 200:
                contenido = response.text.strip()
                
                if codigo == contenido:
                    resultado["existe"] = True
                    resultado["detalle"] = f"✅ Coincidencia EXACTA en archivo"
                    resultado["url_encontrada"] = url
                    return resultado
                elif codigo in contenido:
                    resultado["existe"] = True
                    resultado["detalle"] = f"✅ Coincidencia PARCIAL en archivo"
                    resultado["url_encontrada"] = url
                    return resultado
                    
        except requests.exceptions.SSLError:
            continue
        except requests.exceptions.ConnectionError:
            continue
        except Exception:
            continue
    
    resultado["detalle"] = f"❌ No se encontró ningún archivo .txt con el código"
    return resultado

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def main():
    # Validar argumentos
    if len(sys.argv) < 4:
        print("""
╔══════════════════════════════════════════════════════════════════╗
║              VERIFICADOR DE DOMINIOS                             ║
╚══════════════════════════════════════════════════════════════════╝

USO:
    python verificar.py "CODIGO" "DOMINIO" "METODO"

ARGUMENTOS:
    CODIGO   : Código de verificación (ej: a7G3kL9mN2pQ5rT8vX1zC4bF6hJ9wE0y)
    DOMINIO  : Dominio a verificar (ej: klbrs.es) - SIN http://
    METODO   : DNS o URL

EJEMPLOS:
    python verificar.py "a7G3kL9mN2pQ5rT8vX1zC4bF6hJ9wE0y" "klbrs.es" "DNS"
    python verificar.py "a7G3kL9mN2pQ5rT8vX1zC4bF6hJ9wE0y" "klbrs.es" "URL"
    python verificar.py "MiCodigo123" "ejemplo.com" "DNS"

NOTA: El dominio se usa SIN http:// (solo el nombre del dominio)
        """)
        sys.exit(1)
    
    codigo = sys.argv[1]
    dominio_raw = sys.argv[2]
    metodo = sys.argv[3].upper().strip()
    
    # Limpiar dominio (eliminar http://, https://, barras, etc.)
    dominio = limpiar_dominio(dominio_raw)
    
    # Validar que el código no esté vacío
    if not codigo:
        print("❌ Error: El código no puede estar vacío")
        sys.exit(1)
    
    # Validar longitud del código (opcional, solo advertencia)
    if len(codigo) < 10:
        print(f"⚠️ Advertencia: El código tiene solo {len(codigo)} caracteres (se recomienda 32-43)")
    
    # Validar dominio
    if not dominio or '.' not in dominio:
        print(f"❌ Error: Dominio inválido: '{dominio_raw}'")
        print(f"   Usa solo el nombre del dominio sin http:// (ej: klbrs.es)")
        sys.exit(1)
    
    # Validar método
    if metodo not in ["DNS", "URL"]:
        print("❌ Error: Método inválido. Usa 'DNS' o 'URL'")
        sys.exit(1)
    
    # Mostrar información de la verificación
    print("\n" + "="*60)
    print("🔍 VERIFICACIÓN DE DOMINIO")
    print("="*60)
    print(f"📝 Código    : {codigo}")
    print(f"🌐 Dominio   : {dominio} (original: {dominio_raw})")
    print(f"🔧 Método    : {metodo}")
    print("="*60)
    
    # Ejecutar verificación según método
    if metodo == "DNS":
        resultado = verificar_dns_txt(dominio, codigo)
    else:
        resultado = verificar_url(dominio, codigo)
    
    # Mostrar resultado
    print(f"\n📡 RESULTADO:")
    print(f"   {resultado['detalle']}")
    
    # Mostrar registros TXT si existen (solo para DNS)
    if metodo == "DNS" and resultado.get('registros'):
        print(f"\n📋 Registros TXT encontrados en {dominio}:")
        for r in resultado['registros'][:5]:  # Mostrar máximo 5
            # Truncar si es muy largo
            if len(r) > 80:
                r = r[:77] + "..."
            print(f"   → {r}")
        if len(resultado['registros']) > 5:
            print(f"   ... y {len(resultado['registros']) - 5} registros más")
    
    # Mostrar URL encontrada (solo para URL)
    if metodo == "URL" and resultado.get('url_encontrada'):
        print(f"\n🔗 Archivo encontrado en:")
        print(f"   → {resultado['url_encontrada']}")
    
    # Mensaje final
    print("\n" + "="*60)
    if resultado['existe']:
        print("🎉 VERIFICACIÓN EXITOSA - El código coincide con el registro")
        sys.exit(0)
    else:
        if metodo == "DNS":
            print("❌ VERIFICACIÓN FALLIDA - El código NO está en los registros TXT del dominio")
        else:
            print("❌ VERIFICACIÓN FALLIDA - El código NO está en ningún archivo .txt del dominio")
        sys.exit(1)

if __name__ == "__main__":
    main()
