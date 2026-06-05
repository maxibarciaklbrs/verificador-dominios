from fastapi import FastAPI
from app.api.routes import registro, verificacion, pago, auditoria, confirmacion
from app.config import DIRECTORIO_REPORTES
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="Verificador DNS - klbrs.es", version="2.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
# Montar rutas
app.include_router(registro)
app.include_router(verificacion)
app.include_router(pago)
app.include_router(auditoria)
app.include_router(confirmacion)

# Crear directorios necesarios
os.makedirs(DIRECTORIO_REPORTES, exist_ok=True)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
