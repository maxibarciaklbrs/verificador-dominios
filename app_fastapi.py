from fastapi import FastAPI
from app.database.migrations import init_db
from contextlib import asynccontextmanager
from app.api.routes import registro, verificacion, pago, auditoria, stripe
from app.config import DIRECTORIO_REPORTES
from fastapi.staticfiles import StaticFiles
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Verificador DNS - klbrs.es", version="2.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(registro)
app.include_router(verificacion)
app.include_router(pago)
app.include_router(auditoria)
app.include_router(stripe)

os.makedirs(DIRECTORIO_REPORTES, exist_ok=True)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}
