class PagoError(Exception):
    """
    Error general relacionado con los pagos.
    """
    pass



class UsuarioNoEncontradoError(PagoError):
    """
    El usuario no existe.
    """

    def __init__(
        self,
        email: str
    ):

        super().__init__(
            f"No existe ningún usuario con el email '{email}'."
        )



class UsuarioNoVerificadoError(PagoError):
    """
    El usuario todavía no ha verificado el dominio.
    """

    def __init__(
        self,
        email: str
    ):

        super().__init__(
            f"El usuario '{email}' todavía no ha verificado su dominio."
        )



class PagoNoEncontradoError(PagoError):
    """
    El pago no existe.
    """

    def __init__(
        self,
        pago_id: int
    ):

        super().__init__(
            f"No existe ningún pago con ID '{pago_id}'."
        )



class PagoYaCompletadoError(PagoError):
    """
    El pago ya fue completado.
    """

    def __init__(
        self,
        pago_id: int
    ):

        super().__init__(
            f"El pago '{pago_id}' ya se encuentra completado."
        )



class EstadoPagoInvalidoError(PagoError):
    """
    Estado de pago no permitido.
    """

    def __init__(
        self,
        estado: str
    ):

        super().__init__(
            f"Estado de pago no válido: '{estado}'."
        )



# ==========================================================
# STRIPE
# ==========================================================


class StripeError(PagoError):
    """
    Error comunicando con Stripe.
    """

    def __init__(
        self,
        mensaje: str
    ):

        super().__init__(
            f"Error Stripe: {mensaje}"
        )



class WebhookStripeInvalidoError(PagoError):
    """
    El webhook recibido de Stripe no es válido.
    """

    def __init__(self):

        super().__init__(
            "Webhook Stripe inválido o firma incorrecta."
        )