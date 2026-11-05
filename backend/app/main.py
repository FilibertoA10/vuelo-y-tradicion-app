import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config
from .database import Base, SessionLocal, engine
from .models import User
from .routers import artisans, auth, checkout, products, uploads
from .security import hash_password

logger = logging.getLogger("vuelo_y_tradicion")


def ensure_admin() -> None:
    """Crea el administrador inicial a partir de ADMIN_EMAIL y ADMIN_PASSWORD."""
    if not config.ADMIN_EMAIL or not config.ADMIN_PASSWORD:
        logger.warning("ADMIN_EMAIL/ADMIN_PASSWORD no definidos: no se creó administrador.")
        return
    if len(config.ADMIN_PASSWORD) < 8:
        logger.error("ADMIN_PASSWORD debe tener al menos 8 caracteres; no se creó administrador.")
        return
    with SessionLocal() as db:
        if db.query(User).filter(User.email == config.ADMIN_EMAIL).first() is None:
            db.add(User(email=config.ADMIN_EMAIL, password_hash=hash_password(config.ADMIN_PASSWORD), role="admin"))
            db.commit()
            logger.info("Administrador inicial creado: %s", config.ADMIN_EMAIL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # no-op si init.sql ya creó las tablas
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ensure_admin()
    yield


app = FastAPI(
    title="Vuelo y Tradición API",
    description="Comercio justo con artesanos del Totonacapan. Pedidos directos por WhatsApp.",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(artisans.router)
app.include_router(products.router)
app.include_router(checkout.router)
app.include_router(uploads.router)

# Fotografías subidas por el administrador.
config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")


@app.get("/api/health", tags=["Sistema"])
def health():
    return {"status": "ok"}
