from fastapi import APIRouter, Request
from app.services import verificar_dns_txt
from app.models import marcar_verificado
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/validar-dns")
async def validar_dns(request: Request):
    data = await request.json()
    email = data.get("email")
    codigo = data.get("codigo")
    dominio = data.get("dominio")
    
    resultado = verificar_dns_txt(dominio, codigo)
    
    if resultado["existe"]:
        marcar_verificado(email)
        logger.info(f"✅ Dominio verificado: {email}")
        
        return {
            "exitoso": True,
            "mensaje": f"✅ ¡Dominio verificado! Se encontró el código en los registros TXT de {dominio}"
        }
    else:
        return {
            "exitoso": False,
            "mensaje": f"❌ No se encontró el código en los registros TXT de {dominio}. Verifica que hayas creado el registro TXT correctamente."
        }


@router.post("/estado-verificacion")
async def estado_verificacion(request: Request):
    data = await request.json()
    email = data.get("email")
    
    from app.models import obtener_usuario
    usuario = obtener_usuario(email)
    
    if usuario and usuario.get("verificado", False):
        return {"verificado": True}
    
    return {"verificado": False}
