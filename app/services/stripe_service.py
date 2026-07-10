import stripe
import logging

from app.config import (
    STRIPE_SECRET_KEY,
    STRIPE_SUCCESS_URL,
    STRIPE_CANCEL_URL
)

from app.exceptions.pago_exceptions import PagoError, StripeError


logger = logging.getLogger(__name__)


# ==========================================================
# Inicialización
# ==========================================================

stripe.api_key = STRIPE_SECRET_KEY



# ==========================================================
# Checkout
# ==========================================================

def crear_checkout_session(
    pago_id: int,
    usuario_id: int,
    email: str,
    dominio: str,
    importe: int,
    moneda: str,
    descripcion: str
):
    """
    Crea una sesión Stripe Checkout.

    importe debe venir en céntimos.
    Ejemplo:
        1   = 0,01 €
        100 = 1 €
    """

    try:

        logger.info(
            f"Creando Checkout Stripe para {email}"
        )


        session = stripe.checkout.Session.create(

            mode="payment",


            customer_email=email,


            client_reference_id=str(
                pago_id
            ),


            payment_method_types=[
                "card"
            ],


            line_items=[

                {

                    "price_data": {

                        "currency": moneda,


                        "product_data": {

                            "name": descripcion,

                            "description":
                                f"Dominio: {dominio}"

                        },


                        # Ya viene en céntimos
                        "unit_amount": int(
                            importe
                        )

                    },


                    "quantity": 1

                }

            ],


            metadata={

                "pago_id": str(
                    pago_id
                ),

                "usuario_id": str(
                    usuario_id
                ),

                "email": email,

                "dominio": dominio

            },


            success_url=(
                STRIPE_SUCCESS_URL
                +
                "?session_id={CHECKOUT_SESSION_ID}"
            ),


            cancel_url=STRIPE_CANCEL_URL

        )


        logger.info(
            f"Checkout creado correctamente: {session.id}"
        )


        return session


    except stripe.error.StripeError as e:

        logger.exception(
            "Error creando checkout Stripe"
        )


        raise PagoError(
            "No se pudo crear el pago en Stripe."
        ) from e



# ==========================================================
# Webhooks
# ==========================================================

def construir_evento(
    payload: bytes,
    signature: str,
    webhook_secret: str
):
    """
    Valida la firma enviada por Stripe.
    """

    try:

        return stripe.Webhook.construct_event(
            payload,
            signature,
            webhook_secret
        )


    except stripe.error.SignatureVerificationError as e:

        logger.error(
            "Firma webhook Stripe inválida"
        )

        raise StripeError(
            str(e)
        )



# ==========================================================
# Consultas Stripe
# ==========================================================

def obtener_checkout_session(
    session_id: str
):

    return stripe.checkout.Session.retrieve(
        session_id
    )



def obtener_payment_intent(
    payment_intent_id: str
):

    return stripe.PaymentIntent.retrieve(
        payment_intent_id
    )



def obtener_customer(
    customer_id: str
):

    return stripe.Customer.retrieve(
        customer_id
    )