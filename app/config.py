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

# ==========================================================
# Stripe
# ==========================================================

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

STRIPE_SUCCESS_URL = os.getenv(
    "STRIPE_SUCCESS_URL",
    "http://localhost:8000/pago/exitoso"
)

STRIPE_CANCEL_URL = os.getenv(
    "STRIPE_CANCEL_URL",
    "http://localhost:8000/pago/cancelado"
)


# Cloudflare Turnstile

TURNSTILE_SITE_KEY = os.getenv(
    "TURNSTILE_SITE_KEY",
    "0x4AAAAAADzKNJgXjE6-QvIN"
)

TURNSTILE_SECRET = os.getenv(
    "TURNSTILE_SECRET",
    "0x4AAAAAADzKNP4L7tAfROvFltzV156JRYo"
)

# Archivos
ARCHIVO_PENDIENTES = "pendientes_verificacion.json"
DIRECTORIO_REPORTES = "reportes"

# Dominios bloqueados
DOMINIOS_BLOQUEADOS = [
    'gmail.com', 'googlemail.com', 'hotmail.com', 'outlook.com',
    'live.com', 'msn.com', 'yahoo.com', 'ymail.com', 'rocketmail.com',
    'protonmail.com', 'proton.me', 'mail.com', 'gmx.com', 'aol.com',
    'icloud.com', 'me.com', 'mac.com', 'yandex.com', 'mailinator.com'
]
