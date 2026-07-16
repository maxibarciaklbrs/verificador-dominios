class StripeError(Exception):
    """Error general relacionado con Stripe."""
    pass


class CheckoutSessionError(StripeError):
    """No se pudo crear la Checkout Session."""
    pass


class WebhookError(StripeError):
    """Error procesando un webhook de Stripe."""
    pass