class RegistroError(Exception):
    """
    Excepción base para cualquier error relacionado
    con el registro.
    """
    pass


class DominioInvalidoError(RegistroError):
    def __init__(self, email: str):
        super().__init__(
            f"El email '{email}' no es válido."
        )