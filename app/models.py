import sqlite3
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "verificaciones.db")


def init_db():
    """Inicializa la base de datos"""
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            dominio TEXT NOT NULL,
            codigo TEXT NOT NULL,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_expiracion DATETIME,
            verificado BOOLEAN DEFAULT 0,
            pagado BOOLEAN DEFAULT 0,
            fecha_verificacion DATETIME,
            fecha_pago DATETIME
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ Base de datos SQLite inicializada")


def obtener_codigo_por_dominio(dominio: str):
    """Obtiene código existente para un dominio"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT codigo FROM usuarios WHERE dominio = ? LIMIT 1', (dominio,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Error: {e}")
        return None


def usuario_existe(email: str) -> bool:
    """Verifica si un usuario existe"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM usuarios WHERE email = ?', (email,))
        existe = cursor.fetchone() is not None
        conn.close()
        return existe
    except:
        return False


def crear_usuario(email: str, nombre: str, apellido: str, codigo: str) -> bool:
    """Crea un nuevo usuario"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        dominio = email.split('@')[1]
        fecha_expiracion = (datetime.now() + timedelta(days=7)).isoformat()
        cursor.execute('''
            INSERT INTO usuarios (email, nombre, apellido, dominio, codigo, fecha_expiracion)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (email, nombre, apellido, dominio, codigo, fecha_expiracion))
        conn.commit()
        conn.close()
        logger.info(f"✅ Usuario creado: {email}")
        return True
    except Exception as e:
        logger.error(f"Error creando usuario: {e}")
        return False


def guardar_o_obtener_codigo(email: str, nombre: str, apellido: str):
    """Código único por DOMINIO"""
    dominio = email.split('@')[1].lower()
    
    codigo_existente = obtener_codigo_por_dominio(dominio)
    
    if codigo_existente:
        logger.info(f"📧 Dominio {dominio} ya tiene código")
        if not usuario_existe(email):
            crear_usuario(email, nombre, apellido, codigo_existente)
        return codigo_existente, False
    
    from app.services.codigo_service import generar_codigo_verificacion
    codigo_nuevo = generar_codigo_verificacion()
    crear_usuario(email, nombre, apellido, codigo_nuevo)
    logger.info(f"🆕 Nuevo código para dominio {dominio}")
    return codigo_nuevo, True


def marcar_verificado(email: str):
    """Marca usuario como verificado"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE usuarios 
            SET verificado = 1, fecha_verificacion = ? 
            WHERE email = ?
        ''', (datetime.now().isoformat(), email))
        conn.commit()
        conn.close()
        logger.info(f"✅ Usuario verificado: {email}")
        return True
    except Exception as e:
        logger.error(f"Error marcando verificado: {e}")
        return False


def marcar_pagado(email: str):
    """Marca usuario como pagado"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE usuarios 
            SET pagado = 1, fecha_pago = ? 
            WHERE email = ?
        ''', (datetime.now().isoformat(), email))
        conn.commit()
        conn.close()
        logger.info(f"💰 Usuario marcado como pagado: {email}")
        return True
    except Exception as e:
        logger.error(f"Error marcando pagado: {e}")
        return False


def obtener_usuario(email: str) -> dict:
    """Obtiene datos de un usuario por email"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error obteniendo usuario: {e}")
        return None


def obtener_usuario_por_codigo(codigo: str) -> dict:
    """Obtiene usuario por su código de verificación"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE codigo = ? LIMIT 1', (codigo,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error obteniendo usuario por código: {e}")
        return None


def obtener_todos_usuarios() -> list:
    """Obtiene todos los usuarios"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error obteniendo usuarios: {e}")
        return []
