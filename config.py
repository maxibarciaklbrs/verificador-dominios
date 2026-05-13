# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "reseller2.networksclub.net")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
MI_EMAIL = os.getenv("MI_EMAIL", SMTP_USER)

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Archivos
ARCHIVO_PENDIENTES = "pendientes_verificacion.json"
DIRECTORIO_REPORTES = "reportes"

# Crear directorio de reportes si no existe
os.makedirs(DIRECTORIO_REPORTES, exist_ok=True)
