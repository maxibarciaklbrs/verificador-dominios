from app.database.connection import get_cursor


# ==========================================================
# CREATE
# ==========================================================

def crear_dominio(
    nombre: str,
    codigo: str
) -> int:
    """
    Crea un dominio y devuelve su ID.
    """

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
                nombre,
                codigo
            )
        )

        return cursor.lastrowid


# ==========================================================
# READ
# ==========================================================

def obtener_dominio_por_id(
    dominio_id: int
):

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


def obtener_dominio_por_nombre(
    nombre: str
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM dominios
            WHERE nombre = ?
            """,
            (nombre,)
        )

        row = cursor.fetchone()

        return dict(row) if row else None


def obtener_dominio_por_codigo(
    codigo: str
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM dominios
            WHERE codigo = ?
            """,
            (codigo,)
        )

        row = cursor.fetchone()

        return dict(row) if row else None


def obtener_todos_dominios():

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM dominios
            ORDER BY nombre
            """
        )

        return [dict(row) for row in cursor.fetchall()]


# ==========================================================
# EXISTS
# ==========================================================

def existe_dominio(
    nombre: str
) -> bool:

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT 1
            FROM dominios
            WHERE nombre = ?
            """,
            (nombre,)
        )

        return cursor.fetchone() is not None

# ==========================================================
# DELETE
# ==========================================================

def eliminar_dominio(
    dominio_id: int
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            DELETE FROM dominios
            WHERE id = ?
            """,
            (dominio_id,)
        )