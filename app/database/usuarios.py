from datetime import datetime
from app.database.connection import get_cursor


# ==========================================================
# CREATE
# ==========================================================

def crear_usuario(
    email: str,
    nombre: str,
    apellido: str,
    telefono: str | None,
    dominio_id: int,
    fecha_expiracion: str
) -> int:
    """
    Crea un usuario y devuelve su ID.
    """

    with get_cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO usuarios (
                email,
                nombre,
                apellido,
                telefono,
                dominio_id,
                fecha_expiracion
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                email,
                nombre,
                apellido,
                telefono,
                dominio_id,
                fecha_expiracion
            )
        )

        return cursor.lastrowid


# ==========================================================
# READ
# ==========================================================

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


def obtener_usuario_por_email(email: str):

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM usuarios
            WHERE email = ?
            """,
            (email,)
        )

        row = cursor.fetchone()

        return dict(row) if row else None


def obtener_todos_usuarios():

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM usuarios
            ORDER BY id DESC
            """
        )

        return [dict(row) for row in cursor.fetchall()]


# ==========================================================
# EXISTS
# ==========================================================

def existe_usuario(email: str) -> bool:

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT 1
            FROM usuarios
            WHERE email = ?
            """,
            (email,)
        )

        return cursor.fetchone() is not None


# ==========================================================
# UPDATE
# ==========================================================

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
                email
            )
        )


def actualizar_fecha_expiracion(
    email: str,
    fecha_expiracion: str
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            UPDATE usuarios
            SET fecha_expiracion = ?
            WHERE email = ?
            """,
            (
                fecha_expiracion,
                email
            )
        )


# ==========================================================
# DELETE
# ==========================================================

def eliminar_usuario(email: str):

    with get_cursor() as cursor:

        cursor.execute(
            """
            DELETE FROM usuarios
            WHERE email = ?
            """,
            (email,)
        )

def obtener_pago_completo(
    pago_id: int
):
    """
    Devuelve un pago junto con la información
    del usuario y del dominio asociado.
    """

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT

                p.*,

                u.email,
                u.nombre,
                u.apellido,
                u.telefono,
                u.verificado,

                d.id AS dominio_id,
                d.nombre AS dominio,
                d.codigo

            FROM pagos p

            INNER JOIN usuarios u
                ON p.usuario_id = u.id

            INNER JOIN dominios d
                ON u.dominio_id = d.id

            WHERE p.id = ?

            """,
            (pago_id,)
        )

        row = cursor.fetchone()

        return dict(row) if row else None