import logging
import sqlite3

from app.database.usuarios import (
    obtener_usuario_por_email
)

from app.database.pagos import (
    crear_pago,
    obtener_pago_por_id,
    obtener_pago_por_usuario,
    obtener_pago_por_checkout_session,
    obtener_pago_por_payment_intent,
    obtener_pago_por_evento,
    actualizar_datos_stripe,
    guardar_evento_webhook,
    marcar_pagado,
    actualizar_estado_pago
)

from app.database.dominios import (
    obtener_dominio_por_id
)

from app.services.stripe_service import (
    crear_checkout_session
)

from app.exceptions.pago_exceptions import (
    PagoError,
    UsuarioNoEncontradoError,
    UsuarioNoVerificadoError
)

logger = logging.getLogger(__name__)


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

IMPORTE_ANALISIS = 1      # Stripe trabaja en céntimos (1 = 0,01€)
MONEDA = "eur"
DESCRIPCION = "Análisis de vulnerabilidades"


# ==========================================================
# CREAR PAGO
# ==========================================================

def crear_pago_usuario(
    email: str
) -> dict:
    """
    Crea un pago y genera una sesión Stripe Checkout.

    Flujo:
        Usuario
          |
          v
        Crear registro pago
          |
          v
        Crear Checkout Stripe
          |
          v
        Guardar datos Stripe
          |
          v
        Devolver URL checkout
    """

    try:

        usuario = obtener_usuario_por_email(
            email
        )

        if usuario is None:
            raise UsuarioNoEncontradoError(email)


        if not usuario["verificado"]:
            raise UsuarioNoVerificadoError(email)


        # ==================================================
        # Crear pago interno
        # ==================================================

        pago_id = crear_pago(
            usuario_id=usuario["id"],
            importe=IMPORTE_ANALISIS,
            moneda=MONEDA,
            descripcion=DESCRIPCION
        )


        pago = obtener_pago_por_id(
            pago_id
        )


        if pago is None:

            raise PagoError(
                "No se pudo recuperar el pago creado."
            )


        # ==================================================
        # Obtener dominio
        # ==================================================

        dominio = obtener_dominio_por_id(
            usuario["dominio_id"]
        )


        if dominio is None:

            raise PagoError(
                "El usuario no tiene dominio asociado."
            )


        # ==================================================
        # Crear Stripe Checkout
        # ==================================================

        checkout = crear_checkout_session(
            pago_id=pago["id"],
            usuario_id=usuario["id"],
            email=usuario["email"],
            dominio=dominio["nombre"],
            importe=pago["importe"],
            moneda=pago["moneda"],
            descripcion=pago["descripcion"]
        )


        # ==================================================
        # Guardar datos Stripe
        # ==================================================

        actualizar_datos_stripe(
            pago_id=pago["id"],
            checkout_session_id=checkout.id,
            payment_intent_id=checkout.payment_intent,
            customer_id=checkout.customer
        )


        pago = obtener_pago_por_id(
            pago["id"]
        )


        logger.info(
            f"Pago creado correctamente para {email}"
        )


        return {
            "pago": pago,
            "checkout_url": checkout.url
        }


    except sqlite3.Error as e:

        logger.exception(
            "Error de base de datos creando pago."
        )

        raise PagoError(
            "Error interno creando el pago."
        ) from e



# ==========================================================
# CONSULTAS
# ==========================================================

def obtener_pagos_usuario(
    email: str
) -> list:

    usuario = obtener_usuario_por_email(
        email
    )


    if usuario is None:

        raise UsuarioNoEncontradoError(
            email
        )


    return obtener_pago_por_usuario(
        usuario["id"]
    )



# ==========================================================
# ESTADOS
# ==========================================================

def marcar_pago_completado(
    pago_id: int
):

    marcar_pagado(
        pago_id
    )

    logger.info(
        f"Pago marcado como completado: {pago_id}"
    )



def cambiar_estado_pago(
    pago_id: int,
    estado: str
):

    actualizar_estado_pago(
        pago_id,
        estado
    )

    logger.info(
        f"Estado pago {pago_id}: {estado}"
    )



# ==========================================================
# WEBHOOK STRIPE
# ==========================================================

def procesar_webhook_pago(
    evento: dict
):
    """
    Procesa eventos enviados por Stripe.
    """

    tipo = evento.get(
        "type"
    )

    event_id = evento.get(
        "id"
    )


    logger.info(
        f"Webhook Stripe recibido: {tipo}"
    )


    # ==================================================
    # Evitar eventos duplicados
    # ==================================================

    if event_id:

        evento_existente = obtener_pago_por_evento(
            event_id
        )

        if evento_existente:

            logger.info(
                f"Evento Stripe ya procesado: {event_id}"
            )

            return {
                "ok": True,
                "estado": "duplicado"
            }



    # ==================================================
    # Checkout completado
    # ==================================================

    if tipo == "checkout.session.completed":


        session = evento["data"]["object"]


        pago = obtener_pago_por_checkout_session(
            session["id"]
        )


        if pago is None:

            raise PagoError(
                "No existe pago asociado al checkout."
            )



        # Ya estaba pagado

        if pago["estado"] == "paid":

            return {
                "ok": True,
                "estado": "ya_pagado"
            }



        # Guardar evento

        if event_id:

            guardar_evento_webhook(
                pago["id"],
                event_id
            )



        # Actualizar payment intent si existe

        if session.get(
            "payment_intent"
        ):

            actualizar_datos_stripe(
                pago_id=pago["id"],
                checkout_session_id=session["id"],
                payment_intent_id=session["payment_intent"],
                customer_id=session.get("customer")
            )



        marcar_pagado(
            pago["id"]
        )


        logger.info(
            f"Pago confirmado: {pago['id']}"
        )


        return {
            "ok": True,
            "estado": "pagado"
        }



    # ==================================================
    # Checkout expirado
    # ==================================================

    if tipo == "checkout.session.expired":


        session = evento["data"]["object"]


        pago = obtener_pago_por_checkout_session(
            session["id"]
        )


        if pago:

            actualizar_estado_pago(
                pago["id"],
                "expired"
            )


            if event_id:

                guardar_evento_webhook(
                    pago["id"],
                    event_id
                )


        return {
            "ok": True,
            "estado": "expired"
        }



    # ==================================================
    # Pago fallido
    # ==================================================

    if tipo == "payment_intent.payment_failed":


        intent = evento["data"]["object"]


        pago = obtener_pago_por_payment_intent(
            intent["id"]
        )


        if pago:

            actualizar_estado_pago(
                pago["id"],
                "failed"
            )


            if event_id:

                guardar_evento_webhook(
                    pago["id"],
                    event_id
                )


        return {
            "ok": True,
            "estado": "failed"
        }



    logger.info(
        f"Evento Stripe ignorado: {tipo}"
    )


    return {
        "ok": True,
        "estado": "ignorado"
    }