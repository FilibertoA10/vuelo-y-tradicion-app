"""Pruebas con SQLite temporal: no requieren MySQL. Ejecutar con `pytest` desde backend/."""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="vyt_tests_")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["SECRET_KEY"] = "clave-de-pruebas-clave-de-pruebas"
os.environ["ADMIN_EMAIL"] = "admin@test.mx"
os.environ["ADMIN_PASSWORD"] = "Contrasena-Segura-1"
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:  # dispara lifespan: crea tablas y admin
        yield c


@pytest.fixture(scope="session")
def admin_headers(client):
    r = client.post("/api/auth/login", json={"email": "admin@test.mx", "password": "Contrasena-Segura-1"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
