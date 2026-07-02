class RegistroError(Exception):
    """Error general durante el registro."""
    pass


class DominioInvalidoError(RegistroError):
    """El email no contiene un dominio válido."""
    pass