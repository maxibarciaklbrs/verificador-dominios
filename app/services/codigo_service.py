# app/services/codigo_service.py
import secrets
import string

def generar_codigo_verificacion(longitud: int = 43) -> str:
    """Genera código único de N caracteres (letras, números, - y _)"""
    caracteres = string.ascii_letters + string.digits + "-_"
    codigo = ''.join(secrets.choice(caracteres) for _ in range(longitud))
    return codigo
