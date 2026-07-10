import logging

from app.database.usuarios import (
    marcar_verificado,
    obtener_usuario_por_email
)

from app.database.dominios import (
    obtener_dominio_por_id
)

from app.services.dns_service import verificar_dns_txt

from app.exceptions.verificacion_exceptions import (
    UsuarioNoEncontradoError,
    DominioNoEncontradoError,
    VerificacionDNSError
)

logger = logging.getLogger(__name__)


def verificar_dominio_usuario(email: str) -> dict:
    """
    Verifica el dominio asociado a un usuario.

    El dominio y el código se obtienen desde la base de datos.
    """

    usuario = obtener_usuario_por_email(email)

    if usuario is None:
        raise UsuarioNoEncontradoError(email)

    dominio = obtener_dominio_por_id(
        usuario["dominio_id"]
    )

    if dominio is None:
        raise DominioNoEncontradoError(
            usuario["dominio_id"]
        )

    try:

        resultado_dns = verificar_dns_txt(
            dominio["nombre"],
            dominio["codigo"]
        )

        if not resultado_dns["existe"]:

            return {
                "exitoso": False,
                "mensaje": (
                    f"No se encontró el código en "
                    f"{dominio['nombre']}"
                )
            }

        marcar_verificado(email)

        logger.info(
            f"Dominio verificado: {email}"
        )

        return {
            "exitoso": True,
            "mensaje": (
                f"¡Dominio verificado correctamente!"
            )
        }

    except Exception as e:

        logger.exception(
            "Error verificando DNS."
        )

        raise VerificacionDNSError(
            "No se pudo verificar el dominio."
        ) from e


def obtener_estado_verificacion(
    email: str
) -> dict:
    """
    Devuelve el estado de verificación de un usuario.
    """

    usuario = obtener_usuario_por_email(email)

    if usuario is None:
        raise UsuarioNoEncontradoError(email)

    return {
        "verificado": bool(usuario["verificado"])
    }