import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from .. import config
from ..security import require_admin

router = APIRouter(prefix="/api/admin", tags=["Archivos"])


def detect_image_ext(head: bytes) -> str | None:
    """Identifica el formato por su firma real (no por el nombre ni el Content-Type)."""
    if head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp"
    return None


@router.post("/uploads", dependencies=[Depends(require_admin)])
async def upload_image(file: UploadFile = File(...)):
    """Sube una fotografía (JPG, PNG o WEBP). Devuelve la ruta relativa para guardarla en el producto o taller."""
    max_bytes = config.MAX_UPLOAD_MB * 1024 * 1024
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"La imagen supera {config.MAX_UPLOAD_MB} MB.")
    ext = detect_image_ext(data[:16])
    if ext is None:
        raise HTTPException(status_code=400, detail="Formato no válido. Usa JPG, PNG o WEBP.")

    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    (config.UPLOAD_DIR / name).write_bytes(data)
    return {"url": f"/uploads/{name}"}
