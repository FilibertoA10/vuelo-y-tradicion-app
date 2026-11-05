from collections import OrderedDict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Product
from ..schemas import CheckoutOut, CheckoutRequest, OrderLineOut, WhatsAppOrderOut
from ..whatsapp import build_order_message, build_whatsapp_url

router = APIRouter(prefix="/api/checkout", tags=["Pedidos"])


@router.post("/whatsapp", response_model=CheckoutOut)
def whatsapp_checkout(order: CheckoutRequest, db: Session = Depends(get_db)):
    """Genera un enlace de WhatsApp por cada taller presente en el carrito.

    No cobra ni descuenta inventario: el acuerdo de pago y entrega se hace
    directamente entre comprador y artesano por WhatsApp.
    """
    # Unir líneas repetidas del mismo producto.
    quantities: "OrderedDict[int, int]" = OrderedDict()
    for item in order.items:
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity

    products = (
        db.query(Product)
        .options(joinedload(Product.artisan))
        .filter(Product.id.in_(quantities.keys()))
        .all()
    )
    by_id = {p.id: p for p in products}

    problems = []
    for pid, qty in quantities.items():
        p = by_id.get(pid)
        if p is None or not p.is_active:
            problems.append(f"La pieza #{pid} ya no está disponible.")
        elif qty > p.stock:
            problems.append(f"«{p.title}»: solo hay {p.stock} disponible(s).")
    if problems:
        raise HTTPException(status_code=400, detail=" ".join(problems))

    # Agrupar por taller.
    groups: "OrderedDict[int, list]" = OrderedDict()
    for pid, qty in quantities.items():
        p = by_id[pid]
        groups.setdefault(p.artisan_id, []).append((p, qty))

    orders = []
    for artisan_id, entries in groups.items():
        artisan = entries[0][0].artisan
        lines = [(p.title, qty, float(p.price) * qty) for p, qty in entries]
        total = round(sum(sub for _, _, sub in lines), 2)
        message = build_order_message(
            artisan.full_name, artisan.workshop_name, order.customer_name.strip(),
            lines, total, order.notes,
        )
        orders.append(
            WhatsAppOrderOut(
                artisan_id=artisan_id,
                artisan=artisan.full_name,
                workshop=artisan.workshop_name,
                items=[
                    OrderLineOut(product_id=p.id, title=p.title, quantity=qty, subtotal=round(float(p.price) * qty, 2))
                    for p, qty in entries
                ],
                total=total,
                whatsapp_url=build_whatsapp_url(artisan.phone_whatsapp, message),
            )
        )

    return CheckoutOut(orders=orders, grand_total=round(sum(o.total for o in orders), 2))
