"""Lógica pura (sin dependencias web) para armar los pedidos de WhatsApp."""
import re
import urllib.parse
from typing import Iterable, Optional


def normalize_phone(value: str) -> str:
    """Deja solo dígitos con lada internacional.

    - Acepta "+52 784 000 1122", "784-000-1122", "5217840001122", etc.
    - Un número de 10 dígitos se asume mexicano y recibe el prefijo 52.
    - Lanza ValueError si no tiene entre 10 y 15 dígitos.
    """
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 10:
        digits = "52" + digits
    if not 10 <= len(digits) <= 15:
        raise ValueError("El teléfono debe tener entre 10 y 15 dígitos (con lada).")
    return digits


def format_money(amount: float) -> str:
    return f"${amount:,.2f} MXN"


def build_order_message(
    artisan_name: str,
    workshop: str,
    customer_name: str,
    lines: Iterable[tuple[str, int, float]],
    total: float,
    notes: Optional[str] = None,
) -> str:
    """lines: (titulo, cantidad, subtotal)."""
    parts = [
        f"👋 ¡Hola *{artisan_name}* del taller *{workshop}*!",
        f"Mi nombre es *{customer_name}* y me interesa adquirir estas piezas en "
        "*Vuelo y Tradición*:\n",
    ]
    parts += [f"• {qty}x *{title}* - {format_money(sub)}" for title, qty, sub in lines]
    parts.append(f"\n💰 *Total estimado:* {format_money(total)}")
    if notes:
        parts.append(f"📝 *Notas:* {notes}")
    parts.append("\n¿Tiene disponibilidad y cuál sería el método de entrega y de pago?")
    return "\n".join(parts)


def build_whatsapp_url(phone: str, message: str) -> str:
    return f"https://wa.me/{phone}?text={urllib.parse.quote(message, safe='')}"
