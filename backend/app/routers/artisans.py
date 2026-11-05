from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Artisan, Product
from ..schemas import (
    ArtisanCreate, ArtisanDetail, ArtisanListOut, ArtisanOut, ArtisanUpdate, ProductBrief,
)
from ..security import require_admin
from ..utils import like_pattern

router = APIRouter(prefix="/api/artisans", tags=["Artesanos"])


def _get_or_404(db: Session, artisan_id: int) -> Artisan:
    artisan = db.get(Artisan, artisan_id)
    if artisan is None:
        raise HTTPException(status_code=404, detail="Artesano no encontrado.")
    return artisan


@router.get("", response_model=List[ArtisanListOut])
def list_artisans(
    search: Optional[str] = Query(None, max_length=100, description="Nombre, taller o comunidad"),
    db: Session = Depends(get_db),
):
    """Directorio público de talleres."""
    query = db.query(Artisan)
    if search:
        pattern = like_pattern(search)
        query = query.filter(
            Artisan.full_name.ilike(pattern, escape="\\")
            | Artisan.workshop_name.ilike(pattern, escape="\\")
            | Artisan.community.ilike(pattern, escape="\\")
        )
    artisans = query.order_by(Artisan.workshop_name).all()

    counts = dict(
        db.query(Product.artisan_id, func.count(Product.id))
        .filter(Product.is_active.is_(True))
        .group_by(Product.artisan_id)
        .all()
    )
    result = []
    for a in artisans:
        item = ArtisanListOut.model_validate(a)
        item.product_count = counts.get(a.id, 0)
        result.append(item)
    return result


@router.get("/{artisan_id}", response_model=ArtisanDetail)
def get_artisan(artisan_id: int, db: Session = Depends(get_db)):
    """Perfil del taller con sus piezas activas."""
    artisan = _get_or_404(db, artisan_id)
    products = [ProductBrief.model_validate(p) for p in artisan.products if p.is_active]
    return ArtisanDetail(**ArtisanOut.model_validate(artisan).model_dump(), products=products)


@router.post("", response_model=ArtisanOut, status_code=201, dependencies=[Depends(require_admin)])
def create_artisan(data: ArtisanCreate, db: Session = Depends(get_db)):
    artisan = Artisan(**data.model_dump())
    db.add(artisan)
    db.commit()
    db.refresh(artisan)
    return artisan


@router.put("/{artisan_id}", response_model=ArtisanOut, dependencies=[Depends(require_admin)])
def update_artisan(artisan_id: int, data: ArtisanUpdate, db: Session = Depends(get_db)):
    artisan = _get_or_404(db, artisan_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is None and field in {"full_name", "workshop_name", "community", "phone_whatsapp"}:
            continue  # campos obligatorios: ignorar null
        setattr(artisan, field, value)
    db.commit()
    db.refresh(artisan)
    return artisan


@router.delete("/{artisan_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_artisan(artisan_id: int, db: Session = Depends(get_db)):
    """Elimina el taller y también todas sus piezas."""
    artisan = _get_or_404(db, artisan_id)
    db.delete(artisan)
    db.commit()
    return Response(status_code=204)
