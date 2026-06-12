import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging
from app.services.codigo_service import generar_codigo_verificacion

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "verificaciones.db")

# ==========================================================
# CONEXIÓN
# ==========================================================

@contextmanager
def get_cursor():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        conn.close()

# ==========================================================
# Init + Consultas
# ==========================================================
     

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with get_cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                telefono TEXT,
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

    logger.info("✅ Base de datos SQLite inicializada")


def obtener_codigo_por_dominio(dominio: str):
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT codigo FROM usuarios WHERE dominio = ? LIMIT 1",
                (dominio,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        logger.error(f"Error: {e}")
        return None


def usuario_existe(email: str) -> bool:
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM usuarios WHERE email = ?",
                (email,)
            )
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


def crear_usuario(email: str, nombre: str, apellido: str, telefono: str, codigo: str) -> bool:
    try:
        dominio = email.split("@")[1].lower()
        fecha_expiracion = (datetime.now() + timedelta(days=7)).isoformat()

        with get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO usuarios (
                    email, nombre, apellido, telefono,
                    dominio, codigo, fecha_expiracion
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                email,
                nombre,
                apellido,
                telefono,
                dominio,
                codigo,
                fecha_expiracion
            ))

        logger.info(f"✅ Usuario creado: {email}")
        return True

    except Exception as e:
        logger.error(f"Error creando usuario: {e}")
        return False


def guardar_o_obtener_codigo(email: str, nombre: str, apellido: str, telefono: str):
    dominio = email.split("@")[1].lower()

    codigo_existente = obtener_codigo_por_dominio(dominio)

    if codigo_existente:
        logger.info(f"📧 Dominio {dominio} ya tiene código")

        if not usuario_existe(email):
            crear_usuario(email, nombre, apellido, telefono, codigo_existente)

        return codigo_existente, False

    codigo_nuevo = generar_codigo_verificacion()

    crear_usuario(email, nombre, apellido, telefono, codigo_nuevo)

    logger.info(f"🆕 Nuevo código para dominio {dominio}")

    return codigo_nuevo, True


def marcar_verificado(email: str):
    try:
        with get_cursor() as cursor:
            cursor.execute('''
                UPDATE usuarios
                SET verificado = 1,
                    fecha_verificacion = ?
                WHERE email = ?
            ''', (datetime.now().isoformat(), email))

        return True
    except Exception as e:
        logger.error(f"Error marcando verificado: {e}")
        return False

def marcar_pagado(email: str):
    try:
        with get_cursor() as cursor:
            cursor.execute('''
                UPDATE usuarios
                SET pagado = 1,
                    fecha_pago = ?
                WHERE email = ?
            ''', (datetime.now().isoformat(), email))

        return True
    except Exception as e:
        logger.error(f"Error marcando pagado: {e}")
        return False


def obtener_usuario(email: str):
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM usuarios WHERE email = ?",
                (email,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error: {e}")
        return None


def obtener_usuario_por_codigo(codigo: str):
    print("ENTRO EN OBTENER_USUARIO_POR_CODIGO")
    raise Exception("PRUEBA")
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM usuarios WHERE codigo = ? LIMIT 1",
                (codigo,)
            )
            row = cursor.fetchone()

            print("Tipo:", type(row))
            print("Row:", row)


            return dict(row) if row else None
    except Exception:
        logger.exception("Error obteniendo usuario por código")
        return None


def obtener_todos_usuarios():
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM usuarios ORDER BY id DESC"
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error: {e}")
        return []
