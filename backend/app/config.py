"""Configuración central. Todo sale de variables de entorno (ver .env.example)."""
import logging
import os
import secrets
from pathlib import Path

logger = logging.getLogger("vuelo_y_tradicion")

BASE_DIR = Path(__file__).resolve().parent.parent


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


# Conexión a MySQL. En XAMPP el usuario por defecto es root sin contraseña.
DATABASE_URL = os.getenv(
    "DATABASE_URL", "mysql+pymysql://root:@localhost:3306/vuelo_y_tradicion"
)

# Clave para firmar los tokens JWT del administrador.
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(48)
    logger.warning(
        "SECRET_KEY no está definida: se generó una temporal. "
        "Las sesiones de admin se cerrarán al reiniciar. Defínela en .env."
    )
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "480"))

# Orígenes del frontend autorizados (CORS), separados por coma.
CORS_ORIGINS = _csv(
    os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:5500,http://127.0.0.1:5500,"
        "http://localhost:8080,http://127.0.0.1:8080",
    )
)

# Administrador inicial: se crea al arrancar si no existe.
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip().lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# Subida de fotografías.
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))
