# app/main.py
from fastapi import FastAPI
from app.api.routes import registro, verificacion, pago, auditoria
from app.config import DIRECTORIO_REPORTES
import os

app = FastAPI(title="Verificador DNS", version="2.0")

# Montar rutas
app.include_router(registro.router)
app.include_router(verificacion.router)
app.include_router(pago.router)
app.include_router(auditoria.router)

os.makedirs(DIRECTORIO_REPORTES, exist_ok=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
