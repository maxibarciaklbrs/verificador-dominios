from fastapi import APIRouter, Request
import logging

from app.services.verification_service import (
    verificar_dominio_usuario,
    obtener_estado_verificacion
)

from app.exceptions.verificacion_exceptions import (
    UsuarioNoEncontradoError,
    DominioNoEncontradoError,
    VerificacionError
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/validar-dns")
async def validar_dns(request: Request):

    try:

        data = await request.json()

        return verificar_dominio_usuario(
            email=data["email"]
        )

    except UsuarioNoEncontradoError as e:

        logger.warning(str(e))

        return {
            "exitoso": False,
            "mensaje": str(e)
        }

    except DominioNoEncontradoError as e:

        logger.warning(str(e))

        return {
            "exitoso": False,
            "mensaje": str(e)
        }

    except VerificacionError:

        logger.exception("Error durante la verificación.")

        return {
            "exitoso": False,
            "mensaje": "No se pudo verificar el dominio."
        }


@router.post("/estado-verificacion")
async def estado_verificacion(request: Request):

    try:

        data = await request.json()

        return obtener_estado_verificacion(
            data["email"]
        )

    except UsuarioNoEncontradoError as e:

        logger.warning(str(e))

        return {
            "verificado": False,
            "mensaje": str(e)
        }

    except VerificacionError:

        logger.exception("Error obteniendo estado.")

        return {
            "verificado": False,
            "mensaje": "No se pudo obtener el estado de verificación."
        }