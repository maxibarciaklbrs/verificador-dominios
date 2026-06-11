import re

NAME_REGEX = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]+$")
PHONE_REGEX = re.compile(r"^\+?[1-9]\d{7,14}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

PERSONAL_DOMAINS = {
    "gmail.com",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "yahoo.com",
    "icloud.com",
    "proton.me",
    "protonmail.com",
}


# -------------------------
# Normalización
# -------------------------

def normalize_name(value: str) -> str:
    return " ".join(value.strip().split())


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_phone(value: str) -> str:
    return value.strip()


# -------------------------
# Validaciones
# -------------------------

def validate_name(value: str) -> bool:
    return bool(value) and bool(NAME_REGEX.fullmatch(value))


def validate_email_format(value: str) -> bool:
    return bool(EMAIL_REGEX.fullmatch(value))


def validate_email_corporate(value: str) -> bool:
    domain = value.split("@")[-1]
    return domain not in PERSONAL_DOMAINS


def validate_phone(value: str) -> bool:
    if not value:
        return True  # opcional
    return bool(PHONE_REGEX.fullmatch(value))