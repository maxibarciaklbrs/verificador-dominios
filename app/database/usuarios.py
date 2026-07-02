import logging
from datetime import datetime, timedelta

from app.database.connection import get_cursor

logger = logging.getLogger(__name__)

def crear_usuario(
    email: str,
    nombre: str,
    apellido: str,
    telefono: str,
    dominio_id: int
):

    fecha_expiracion = (
        datetime.now() + timedelta(days=7)
    ).isoformat()

    with get_cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO usuarios (

                dominio_id,
                email,
                nombre,
                apellido,
                telefono,
                fecha_expiracion

            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                dominio_id,
                email.lower(),
                nombre,
                apellido,
                telefono,
                fecha_expiracion
            )
        )

        return cursor.lastrowid


def obtener_usuario(email: str):
    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM usuarios
            WHERE email = ?
            """,
            (email.lower(),)
        )

        row = cursor.fetchone()

        return dict(row) if row else None


def obtener_usuario_por_id(usuario_id: int):
    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM usuarios
            WHERE id = ?
            """,
            (usuario_id,)
        )

        row = cursor.fetchone()

        return dict(row) if row else None


def obtener_usuario_por_codigo(codigo: str):
    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT u.*

            FROM usuarios u

            INNER JOIN dominios d
                ON d.id = u.dominio_id

            WHERE d.codigo = ?

            LIMIT 1
            """,
            (codigo,)
        )

        row = cursor.fetchone()

        return dict(row) if row else None


def marcar_verificado(email: str):
    with get_cursor() as cursor:

        cursor.execute(
            """
            UPDATE usuarios

            SET
                verificado = 1,
                fecha_verificacion = ?

            WHERE email = ?
            """,
            (
                datetime.now().isoformat(),
                email.lower()
            )
        )


def obtener_todos_usuarios():
    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM usuarios
            ORDER BY id DESC
            """
        )

        rows = cursor.fetchall()

        return [dict(row) for row in rows]