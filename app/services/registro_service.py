import logging
import sqlite3

from app.database.dominios import (
    obtener_dominio_por_nombre,
    obtener_dominio_por_id,
    crear_dominio
)

from app.database.usuarios import (
    obtener_usuario,
    obtener_usuario_por_id,
    crear_usuario
)

from app.exceptions.registro_exceptions import (
    RegistroError,
    DominioInvalidoError
)

from app.services.codigo_service import generar_codigo_verificacion

from app.validations.validations import (
    normalize_email,
    obtener_dominio_email,
    validate_email_format
)

logger = logging.getLogger(__name__)


def registrar_usuario(
    email: str,
    nombre: str,
    apellido: str,
    telefono: str
):
    """
    Registra un usuario.

    Si el dominio no existe se crea junto con un código.
    Si el usuario no existe se crea.

    Devuelve un diccionario con la información del registro.
    """

    email = normalize_email(email)

    if not validate_email_format(email):
        raise DominioInvalidoError(
            f"Email inválido: {email}"
        )

    try:

        # ==================================================
        # Dominio
        # ==================================================

        dominio_nombre = obtener_dominio_email(email)

        dominio = obtener_dominio_por_nombre(
            dominio_nombre
        )

        dominio_creado = False

        if dominio is None:

            codigo = generar_codigo_verificacion()

            dominio_id = crear_dominio(
                dominio_nombre,
                codigo
            )

            dominio = obtener_dominio_por_id(
                dominio_id
            )

            dominio_creado = True

            logger.info(
                f"Nuevo dominio creado: {dominio_nombre}"
            )

        # ==================================================
        # Usuario
        # ==================================================

        usuario = obtener_usuario(email)

        usuario_creado = False

        if usuario is None:

            usuario_id = crear_usuario(
                email=email,
                nombre=nombre,
                apellido=apellido,
                telefono=telefono,
                dominio_id=dominio["id"]
            )

            usuario = obtener_usuario_por_id(
                usuario_id
            )

            usuario_creado = True

            logger.info(
                f"Usuario creado: {email}"
            )

        else:

            logger.info(
                f"Usuario existente: {email}"
            )

        # ==================================================
        # Resultado
        # ==================================================

        return {
            "usuario": usuario,
            "dominio": dominio,
            "usuario_creado": usuario_creado,
            "dominio_creado": dominio_creado
        }

    except sqlite3.Error as e:

        logger.exception(
            "Error de base de datos durante el registro."
        )

        raise RegistroError(
            "No se pudo completar el registro."
        ) from e