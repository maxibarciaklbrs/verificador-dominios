import json
import os
import logging
from datetime import datetime, timedelta
from app.services.codigo_service import generar_codigo_verificacion

logger = logging.getLogger(__name__)
ARCHIVO_PENDIENTES = "pendientes_verificacion.json"


def cargar_pendientes() -> dict:
    """Carga el archivo JSON de usuarios pendientes"""
    if os.path.exists(ARCHIVO_PENDIENTES):
        with open(ARCHIVO_PENDIENTES, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar_pendientes(pendientes: dict) -> None:
    """Guarda el archivo JSON de usuarios pendientes"""
    with open(ARCHIVO_PENDIENTES, "w", encoding="utf-8") as f:
        json.dump(pendientes, f, indent=2, ensure_ascii=False)


def guardar_o_obtener_codigo(email: str, nombre: str, apellido: str, telefono: str) -> tuple:
    """
    Devuelve el código existente o crea uno nuevo si no existe
    
    Returns:
        (codigo, es_nuevo)
    """
    pendientes = cargar_pendientes()
    
    if email in pendientes:
        logger.info(f"📧 Email {email} ya existe. Usando código existente")
        return pendientes[email]["codigo"], False
    
    codigo = generar_codigo_verificacion()
    pendientes[email] = {
        "codigo": codigo,
        "nombre": nombre,
        "apellido": apellido,
        "telefono": telefono,
        "dominio": email.split('@')[1],
        "fecha_registro": datetime.now().isoformat(),
        "fecha_expiracion": (datetime.now() + timedelta(days=7)).isoformat(),
        "verificado": False,
        "pagado": False
    }
    
    guardar_pendientes(pendientes)
    logger.info(f"🆕 Nuevo código creado para {email}")
    return codigo, True


def actualizar_verificacion(email: str, verificado: bool = True) -> bool:
    """Marca un usuario como verificado"""
    pendientes = cargar_pendientes()
    
    if email in pendientes:
        pendientes[email]["verificado"] = verificado
        if verificado:
            pendientes[email]["fecha_verificacion"] = datetime.now().isoformat()
        guardar_pendientes(pendientes)
        logger.info(f"✅ Usuario {email} verificado = {verificado}")
        return True
    
    return False


def actualizar_pago(email: str, pagado: bool = True, monto: float = 50.0) -> bool:
    """Marca un usuario como pagado y registra el pago"""
    pendientes = cargar_pendientes()
    
    if email in pendientes:
        pendientes[email]["pagado"] = pagado
        if pagado:
            pendientes[email]["fecha_pago"] = datetime.now().isoformat()
            pendientes[email]["monto_pago"] = monto
        guardar_pendientes(pendientes)
        
        # Log de pago
        usuario = pendientes[email]
        with open("pagos_registrados.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | {email} | {usuario['nombre']} | {usuario['apellido']} | MONTO: ${monto}\n")
        
        logger.info(f"💰 Pago registrado: {email} - ${monto}")
        return True
    
    return False


def obtener_usuario_por_codigo(codigo: str) -> tuple:
    """Busca un usuario por su código de verificación. Retorna (email, datos) o (None, None)"""
    pendientes = cargar_pendientes()
    
    for email, datos in pendientes.items():
        if datos.get("codigo") == codigo:
            return email, datos
    
    return None, None


def registrar_log_registro(nombre: str, apellido: str, email: str, telefono:str, codigo: str, es_nuevo: bool) -> None:
    """Registra en archivo de logs cada nuevo registro o reutilización"""
    with open("registros.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | {nombre} {apellido} | {email} | {telefono}| CODIGO: {codigo} | {'NUEVO' if es_nuevo else 'REUTILIZADO'}\n")
