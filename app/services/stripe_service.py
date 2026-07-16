import stripe
<<<<<<< HEAD
import os
from dotenv import load_dotenv

load_dotenv()

# Configurar Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class StripePaymentService:
    def __init__(self):
        self.secret_key = os.getenv("STRIPE_SECRET_KEY")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        self.success_url = os.getenv("STRIPE_SUCCESS_URL", "http://localhost:8000/pago-exitoso")
        self.cancel_url = os.getenv("STRIPE_CANCEL_URL", "http://localhost:8000/pago-cancelado")
    
    def create_checkout_session(self, email: str, amount: float = 9.99, currency: str = "eur", 
                                 verification_code: str = None):
        """
        Crea una sesión de checkout de Stripe
        """
        try:
            # Convertir a centavos (Stripe trabaja con la unidad más pequeña)
            amount_cents = int(amount * 100)
            
            # Metadata para identificar la transacción
            metadata = {
                "email": email,
                "verification_code": verification_code or "unknown"
            }
            
            # Crear la sesión
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": "Escaneo de Vulnerabilidades",
                            "description": f"Verificación y escaneo de seguridad para: {email}",
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=f"{self.success_url}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{self.cancel_url}?session_id={{CHECKOUT_SESSION_ID}}",
                customer_email=email,
                metadata=metadata,
                payment_intent_data={
                    "metadata": metadata
                }
            )
            
            return {
                "success": True,
                "session_id": session.id,
                "checkout_url": session.url,
                "payment_intent": session.payment_intent
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error inesperado: {str(e)}"
            }
    
    def get_session_status(self, session_id: str):
        """
        Obtiene el estado de una sesión de checkout
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            return {
                "success": True,
                "status": session.status,
                "payment_status": session.payment_status,
                "customer_email": session.customer_email,
                "metadata": session.metadata
            }
            
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_webhook(self, payload: str, sig_header: str):
        """
        Procesa un webhook de Stripe
        """
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            # Procesar según el tipo de evento
            if event["type"] == "checkout.session.completed":
                session = event["data"]["object"]
                
                # Extraer datos
                email = session.get("customer_email")
                verification_code = session.get("metadata", {}).get("verification_code")
                session_id = session.get("id")
                
                # Aquí es donde actualizamos el estado en tu BD
                return {
                    "success": True,
                    "event_type": "payment_successful",
                    "email": email,
                    "verification_code": verification_code,
                    "session_id": session_id,
                    "message": "Pago completado exitosamente"
                }
                
            elif event["type"] == "checkout.session.expired":
                return {
                    "success": True,
                    "event_type": "payment_expired",
                    "message": "La sesión de pago expiró"
                }
            
            return {
                "success": True,
                "event_type": event["type"],
                "message": "Evento procesado"
            }
            
        except stripe.error.SignatureVerificationError:
            return {
                "success": False,
                "error": "Firma de webhook inválida"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error procesando webhook: {str(e)}"
            }

# Instancia global
stripe_service = StripePaymentService()
=======
import logging

from app.config import STRIPE_SECRET_KEY, STRIPE_SUCCESS_URL, STRIPE_CANCEL_URL

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
    descripcion: str,
):
    """
    Crea una sesión Stripe Checkout.

    importe debe venir en céntimos.
    Ejemplo:
        1   = 0,01 €
        100 = 1 €
    """

    try:

        logger.info(f"Creando Checkout Stripe para {email}")

        session = stripe.checkout.Session.create(
            mode="payment",
            customer_email=email,
            client_reference_id=str(pago_id),
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": moneda,
                        "product_data": {
                            "name": descripcion,
                            "description": f"Dominio: {dominio}",
                        },
                        # Ya viene en céntimos
                        "unit_amount": int(importe),
                    },
                    "quantity": 20,
                }
            ],
            metadata={
                "pago_id": str(pago_id),
                "usuario_id": str(usuario_id),
                "email": email,
                "dominio": dominio,
            },
            success_url=(STRIPE_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}"),
            cancel_url=STRIPE_CANCEL_URL,
        )

        logger.info(f"Checkout creado correctamente: {session.id}")

        return session

    except stripe.error.StripeError as e:

        logger.exception("Error creando checkout Stripe")

        raise PagoError("No se pudo crear el pago en Stripe.") from e


# ==========================================================
# Webhooks
# ==========================================================


def construir_evento(payload: bytes, signature: str, webhook_secret: str):
    """
    Valida la firma enviada por Stripe.
    """

    try:

        return stripe.Webhook.construct_event(payload, signature, webhook_secret)

    except stripe.error.SignatureVerificationError as e:

        logger.error("Firma webhook Stripe inválida")

        raise StripeError(str(e))


# ==========================================================
# Consultas Stripe
# ==========================================================


def obtener_checkout_session(session_id: str):

    return stripe.checkout.Session.retrieve(session_id)


def obtener_payment_intent(payment_intent_id: str):

    return stripe.PaymentIntent.retrieve(payment_intent_id)


def obtener_customer(customer_id: str):

    return stripe.Customer.retrieve(customer_id)
>>>>>>> dev
