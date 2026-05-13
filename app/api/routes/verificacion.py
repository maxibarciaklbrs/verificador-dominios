from fastapi import APIRouter, Request
from app.services import verificar_dns_txt
from app.config import ARCHIVO_PENDIENTES
import json
from datetime import datetime

router = APIRouter()


@router.post("/validar-dns")
async def validar_dns(request: Request):
    data = await request.json()
    email = data.get("email")
    codigo = data.get("codigo")
    dominio = data.get("dominio")
    
    resultado = verificar_dns_txt(dominio, codigo)
    
    if resultado["existe"]:
        try:
            with open(ARCHIVO_PENDIENTES, "r") as f:
                pendientes = json.load(f)
            if email in pendientes:
                pendientes[email]["verificado"] = True
                pendientes[email]["fecha_verificacion"] = datetime.now().isoformat()
                with open(ARCHIVO_PENDIENTES, "w") as f:
                    json.dump(pendientes, f, indent=2, ensure_ascii=False)
        except:
            pass
        
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
    
    try:
        with open(ARCHIVO_PENDIENTES, "r") as f:
            pendientes = json.load(f)
        if email in pendientes and pendientes[email].get("verificado", False):
            return {"verificado": True}
    except:
        pass
    
    return {"verificado": False}

