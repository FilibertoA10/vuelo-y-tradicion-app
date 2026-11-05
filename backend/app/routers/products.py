from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Artisan, Product
from ..schemas import ProductCreate, ProductOut, ProductUpdate
from ..security import require_admin
from ..utils import like_pattern

router = APIRouter(prefix="/api", tags=["Productos"])


def _get_or_404(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return product


def _check_artisan(db: Session, artisan_id: int) -> None:
    if db.get(Artisan, artisan_id) is None:
        raise HTTPException(status_code=400, detail="El artesano indicado no existe.")


def _filtered(db: Session, search, category, artisan_id, only_active: bool):
    query = db.query(Product).options(joinedload(Product.artisan))
    if only_active:
        query = query.filter(Product.is_active.is_(True))
    if category:
        query = query.filter(Product.category == category)
    if artisan_id:
        query = query.filter(Product.artisan_id == artisan_id)
    if search:
        pattern = like_pattern(search)
        query = query.filter(
            Product.title.ilike(pattern, escape="\\")
            | Product.description.ilike(pattern, escape="\\")
        )
    return query.order_by(Product.id.desc()).all()


# ---------- Público ----------
@router.get("/products", response_model=List[ProductOut])
def list_products(
    search: Optional[str] = Query(None, max_length=100, description="Título o descripción"),
    category: Optional[str] = Query(None, max_length=60),
    artisan_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    return _filtered(db, search, category, artisan_id, only_active=True)


@router.get("/categories", response_model=List[str])
def list_categories(db: Session = Depends(get_db)):
    rows = (
        db.query(Product.category)
        .filter(Product.is_active.is_(True))
        .distinct()
        .order_by(Product.category)
        .all()
    )
    return [r[0] for r in rows]


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = _get_or_404(db, product_id)
    if not product.is_active:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return product


# ---------- Administrador (CRUD) ----------
@router.get("/admin/products", response_model=List[ProductOut], dependencies=[Depends(require_admin)])
def admin_list_products(
    search: Optional[str] = Query(None, max_length=100),
    category: Optional[str] = Query(None, max_length=60),
    artisan_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Inventario completo, incluidas las piezas ocultas."""
    return _filtered(db, search, category, artisan_id, only_active=False)


@router.post("/products", response_model=ProductOut, status_code=201, dependencies=[Depends(require_admin)])
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    _check_artisan(db, data.artisan_id)
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=ProductOut, dependencies=[Depends(require_admin)])
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)):
    product = _get_or_404(db, product_id)
    changes = data.model_dump(exclude_unset=True)
    if changes.get("artisan_id") is not None:
        _check_artisan(db, changes["artisan_id"])
    for field, value in changes.items():
        if value is None:
            continue  # ningún campo del producto admite null
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = _get_or_404(db, product_id)
    db.delete(product)
    db.commit()
    return Response(status_code=204)
