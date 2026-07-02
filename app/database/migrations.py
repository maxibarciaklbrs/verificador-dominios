import logging
import os

from app.database.connection import get_cursor

logger = logging.getLogger(__name__)


def init_db():
    with get_cursor() as cursor:

        # ==========================
        # Tabla dominios
        # ==========================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dominios (
                       
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                codigo TEXT NOT NULL UNIQUE,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
               
            )
        """)

        # ==========================
        # Tabla usuarios
        # ==========================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (

                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dominio_id INTEGER NOT NULL,
                       
                email TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                telefono TEXT,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_expiracion DATETIME,
                verificado INTEGER DEFAULT 0,
                fecha_verificacion DATETIME,

                FOREIGN KEY (dominio_id)
                    REFERENCES dominios(id)
            )
        """)

        # ==========================
        # Tabla pagos
        # ==========================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagos (
                       
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                estado TEXT NOT NULL DEFAULT 'pending',
                importe INTEGER NOT NULL,
                moneda TEXT NOT NULL DEFAULT 'eur',
                stripe_checkout_session_id TEXT UNIQUE,
                stripe_payment_intent TEXT UNIQUE,
                stripe_event_id TEXT UNIQUE,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_pago DATETIME,
                
                FOREIGN KEY(usuario_id)
                    REFERENCES usuarios(id)
                
            )
        """)

    logger.info("✅ Base de datos inicializada correctamente")