class VerificacionError(Exception):
    """
    Excepción base para cualquier error relacionado
    con la verificación del dominio.
    """
    pass


class UsuarioNoEncontradoError(VerificacionError):
    def __init__(self, email: str):
        super().__init__(
            f"No existe ningún usuario con el email '{email}'."
        )


class DominioNoEncontradoError(VerificacionError):
    def __init__(self, dominio_id: int):
        super().__init__(
            f"No existe ningún dominio con id {dominio_id}."
        )


class VerificacionDNSError(VerificacionError):
    def __init__(self, mensaje: str = "Error durante la verificación DNS."):
        super().__init__(mensaje)