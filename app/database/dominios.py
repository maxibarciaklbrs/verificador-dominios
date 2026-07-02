import logging

from app.database.connection import get_cursor

logger = logging.getLogger(__name__)


def obtener_dominio_por_nombre(nombre: str):
    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM dominios
            WHERE nombre = ?
            """,
            (nombre.lower(),)
        )

        row = cursor.fetchone()

        return dict(row) if row else None


def obtener_dominio_por_id(dominio_id: int):
    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM dominios
            WHERE id = ?
            """,
            (dominio_id,)
        )

        row = cursor.fetchone()

        return dict(row) if row else None


def crear_dominio(nombre: str, codigo: str):
    with get_cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO dominios (
                nombre,
                codigo
            )
            VALUES (?, ?)
            """,
            (
                nombre.lower(),
                codigo
            )
        )

        return cursor.lastrowid