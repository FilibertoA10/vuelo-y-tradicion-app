import pytest

from app.whatsapp import build_order_message, build_whatsapp_url, normalize_phone


def test_normalize_phone_variants():
    assert normalize_phone("+52 784 000 1122") == "527840001122"
    assert normalize_phone("784-000-1122") == "527840001122"
    assert normalize_phone("5217840001122") == "5217840001122"


@pytest.mark.parametrize("bad", ["", "123", "abc", "1" * 16])
def test_normalize_phone_rejects_invalid(bad):
    with pytest.raises(ValueError):
        normalize_phone(bad)


def test_message_and_url_encoding():
    msg = build_order_message("Ana", "Taller X", "Luis", [("Blusa", 2, 1700.0)], 1700.0, "Talla M & envío")
    assert "2x *Blusa*" in msg and "$1,700.00 MXN" in msg and "Talla M & envío" in msg
    url = build_whatsapp_url("5217840001122", msg)
    assert url.startswith("https://wa.me/5217840001122?text=")
    assert " " not in url and "&" not in url.split("?text=")[1]
