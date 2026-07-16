from datetime import datetime

from app.database.connection import get_cursor



# ==========================================================
# CREATE
# ==========================================================

def crear_pago(
    usuario_id: int,
    importe: int,
    descripcion: str,
    moneda: str = "eur"
) -> int:

    with get_cursor() as cursor:

        cursor.execute(
            """
            INSERT INTO pagos (
                usuario_id,
                importe,
                moneda,
                descripcion,
                estado
            )
            VALUES (?, ?, ?, ?, 'pending')
            """,
            (
                usuario_id,
                importe,
                moneda,
                descripcion
            )
        )

        return cursor.lastrowid



# ==========================================================
# READ
# ==========================================================

def obtener_pago_por_id(
    pago_id: int
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM pagos
            WHERE id = ?
            """,
            (pago_id,)
        )

        row = cursor.fetchone()

        return dict(row) if row else None



def obtener_pago_por_usuario(
    usuario_id: int
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM pagos
            WHERE usuario_id = ?
            ORDER BY fecha_creacion DESC
            """,
            (usuario_id,)
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]



def obtener_pago_activo_por_usuario(
    usuario_id: int
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM pagos
            WHERE usuario_id = ?
            AND estado IN ('pending','checkout')
            ORDER BY fecha_creacion DESC
            LIMIT 1
            """,
            (usuario_id,)
        )

        row = cursor.fetchone()

        return dict(row) if row else None



def obtener_pago_por_checkout_session(
    checkout_session_id: str
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM pagos
            WHERE stripe_checkout_session_id = ?
            """,
            (checkout_session_id,)
        )

        row = cursor.fetchone()

        return dict(row) if row else None



def obtener_pago_por_payment_intent(
    payment_intent_id: str
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM pagos
            WHERE stripe_payment_intent_id = ?
            """,
            (payment_intent_id,)
        )

        row = cursor.fetchone()

        return dict(row) if row else None



def obtener_pago_por_evento(
    event_id: str
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            SELECT *
            FROM pagos
            WHERE stripe_event_id = ?
            """,
            (event_id,)
        )

        row = cursor.fetchone()

        return dict(row) if row else None



# ==========================================================
# UPDATE STRIPE
# ==========================================================

def actualizar_datos_stripe(
    pago_id: int,
    checkout_session_id: str,
    payment_intent_id: str | None,
    customer_id: str | None
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            UPDATE pagos
            SET
                stripe_checkout_session_id = ?,
                stripe_payment_intent_id = ?,
                stripe_customer_id = ?,
                estado = 'checkout'
            WHERE id = ?
            """,
            (
                checkout_session_id,
                payment_intent_id,
                customer_id,
                pago_id
            )
        )



def guardar_evento_webhook(
    pago_id: int,
    event_id: str
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            UPDATE pagos
            SET stripe_event_id = ?
            WHERE id = ?
            """,
            (
                event_id,
                pago_id
            )
        )



# ==========================================================
# ESTADOS
# ==========================================================

def actualizar_estado_pago(
    pago_id: int,
    estado: str
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            UPDATE pagos
            SET estado = ?
            WHERE id = ?
            """,
            (
                estado,
                pago_id
            )
        )



def marcar_pagado(
    pago_id: int
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            UPDATE pagos
            SET
                estado = 'paid',
                fecha_pago = ?
            WHERE id = ?
            """,
            (
                datetime.now().isoformat(),
                pago_id
            )
        )



# ==========================================================
# DELETE
# ==========================================================

def eliminar_pago(
    pago_id: int
):

    with get_cursor() as cursor:

        cursor.execute(
            """
            DELETE FROM pagos
            WHERE id = ?
            """,
            (pago_id,)
        )