from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DATABASE_URL

_engine_args = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    # Permite correr las pruebas con SQLite en memoria/archivo.
    _engine_args = {"connect_args": {"check_same_thread": False}}

engine = create_engine(DATABASE_URL, **_engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
