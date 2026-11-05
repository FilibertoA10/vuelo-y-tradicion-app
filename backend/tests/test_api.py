import io

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def _artisan(client, headers, name="Herminia García", phone="784 000 1122"):
    r = client.post("/api/artisans", headers=headers, json={
        "full_name": name, "workshop_name": f"Taller de {name}", "community": "Papantla",
        "bio": "Tejedora", "phone_whatsapp": phone,
    })
    assert r.status_code == 201, r.text
    return r.json()


def _product(client, headers, artisan_id, **kw):
    data = {"artisan_id": artisan_id, "title": "Blusa bordada", "description": "Punto de cruz",
            "category": "Textiles", "price": 850, "stock": 4, "image_url": "/uploads/x.png"}
    data.update(kw)
    r = client.post("/api/products", headers=headers, json=data)
    assert r.status_code == 201, r.text
    return r.json()


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_login_and_protection(client, admin_headers):
    assert client.post("/api/auth/login", json={"email": "admin@test.mx", "password": "mala"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "nadie@test.mx", "password": "mala"}).status_code == 401
    assert client.get("/api/auth/me", headers=admin_headers).json()["role"] == "admin"
    # Sin token no se puede escribir.
    assert client.post("/api/products", json={}).status_code == 401
    assert client.post("/api/artisans", json={}).status_code == 401
    assert client.get("/api/admin/products").status_code == 401
    assert client.post("/api/auth/login", json={"email": "a", "password": "b"}).status_code in (401, 422)


def test_artisan_directory_and_crud(client, admin_headers):
    a = _artisan(client, admin_headers)
    assert a["phone_whatsapp"] == "527840001122"  # normalizado

    listing = client.get("/api/artisans").json()
    assert any(x["id"] == a["id"] for x in listing)
    assert client.get("/api/artisans", params={"search": "papantla"}).json()
    assert client.get("/api/artisans", params={"search": "%"}).json() == []  # % se trata literal

    r = client.put(f"/api/artisans/{a['id']}", headers=admin_headers, json={"community": "Coxquihui"})
    assert r.json()["community"] == "Coxquihui"
    assert client.put("/api/artisans/99999", headers=admin_headers, json={}).status_code == 404

    bad = client.post("/api/artisans", headers=admin_headers, json={
        "full_name": "X Y", "workshop_name": "T", "community": "C", "phone_whatsapp": "12"})
    assert bad.status_code == 422


def test_product_crud_search_and_filters(client, admin_headers):
    a = _artisan(client, admin_headers, "Marta López")
    p = _product(client, admin_headers, a["id"], title="Extracto de vainilla", category="Vainilla", price=380)
    hidden = _product(client, admin_headers, a["id"], title="Pieza oculta", is_active=False)

    public = client.get("/api/products").json()
    ids = [x["id"] for x in public]
    assert p["id"] in ids and hidden["id"] not in ids
    assert client.get(f"/api/products/{hidden['id']}").status_code == 404

    admin_ids = [x["id"] for x in client.get("/api/admin/products", headers=admin_headers).json()]
    assert hidden["id"] in admin_ids

    assert [x["id"] for x in client.get("/api/products", params={"search": "vainilla"}).json()] == [p["id"]]
    assert client.get("/api/products", params={"category": "Vainilla", "artisan_id": a["id"]}).json()[0]["id"] == p["id"]
    assert "Vainilla" in client.get("/api/categories").json()

    r = client.put(f"/api/products/{p['id']}", headers=admin_headers, json={"price": 400, "stock": 9})
    assert r.json()["price"] == 400 and r.json()["stock"] == 9
    assert client.post("/api/products", headers=admin_headers, json={
        "artisan_id": 99999, "title": "Zz", "description": "Zz", "category": "Zz",
        "price": 1, "image_url": "/a.png"}).status_code == 400
    assert client.post("/api/products", headers=admin_headers, json={
        "artisan_id": a["id"], "title": "Zz", "description": "Zz", "category": "Zz",
        "price": -5, "image_url": "/a.png"}).status_code == 422

    assert client.delete(f"/api/products/{p['id']}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/products/{p['id']}").status_code == 404


def test_artisan_detail_hides_inactive_and_cascade_delete(client, admin_headers):
    a = _artisan(client, admin_headers, "Rosa Pérez")
    shown = _product(client, admin_headers, a["id"])
    _product(client, admin_headers, a["id"], title="Oculta", is_active=False)
    detail = client.get(f"/api/artisans/{a['id']}").json()
    assert [p["id"] for p in detail["products"]] == [shown["id"]]

    assert client.delete(f"/api/artisans/{a['id']}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/artisans/{a['id']}").status_code == 404
    assert client.get(f"/api/products/{shown['id']}").status_code == 404


def test_checkout_groups_by_artisan(client, admin_headers):
    a1 = _artisan(client, admin_headers, "Uno Uno", "784 111 1111")
    a2 = _artisan(client, admin_headers, "Dos Dos", "784 222 2222")
    p1 = _product(client, admin_headers, a1["id"], price=100, stock=5)
    p2 = _product(client, admin_headers, a2["id"], price=50.5, stock=5)

    r = client.post("/api/checkout/whatsapp", json={
        "customer_name": "Ana Pérez", "notes": "Envío a Xalapa",
        "items": [{"product_id": p1["id"], "quantity": 2}, {"product_id": p2["id"], "quantity": 1},
                  {"product_id": p1["id"], "quantity": 1}]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["orders"]) == 2
    by_artisan = {o["artisan_id"]: o for o in body["orders"]}
    assert by_artisan[a1["id"]]["total"] == 300  # líneas repetidas se suman
    assert by_artisan[a1["id"]]["whatsapp_url"].startswith("https://wa.me/527841111111?text=")
    assert by_artisan[a2["id"]]["whatsapp_url"].startswith("https://wa.me/527842222222?text=")
    assert body["grand_total"] == 350.5


def test_checkout_validation(client, admin_headers):
    a = _artisan(client, admin_headers, "Tres Tres")
    p = _product(client, admin_headers, a["id"], stock=2)
    off = _product(client, admin_headers, a["id"], is_active=False)

    over = client.post("/api/checkout/whatsapp", json={"customer_name": "Ana", "items": [{"product_id": p["id"], "quantity": 3}]})
    assert over.status_code == 400 and "disponible" in over.json()["detail"]
    gone = client.post("/api/checkout/whatsapp", json={"customer_name": "Ana", "items": [{"product_id": off["id"], "quantity": 1}]})
    assert gone.status_code == 400
    missing = client.post("/api/checkout/whatsapp", json={"customer_name": "Ana", "items": [{"product_id": 99999, "quantity": 1}]})
    assert missing.status_code == 400
    empty = client.post("/api/checkout/whatsapp", json={"customer_name": "Ana", "items": []})
    assert empty.status_code == 422
    zero = client.post("/api/checkout/whatsapp", json={"customer_name": "Ana", "items": [{"product_id": p["id"], "quantity": 0}]})
    assert zero.status_code == 422


def test_upload_image(client, admin_headers):
    ok = client.post("/api/admin/uploads", headers=admin_headers, files={"file": ("foto.png", io.BytesIO(PNG), "image/png")})
    assert ok.status_code == 200
    url = ok.json()["url"]
    assert url.startswith("/uploads/") and url.endswith(".png")
    assert client.get(url).status_code == 200

    fake = client.post("/api/admin/uploads", headers=admin_headers, files={"file": ("a.png", io.BytesIO(b"<script>x</script>"), "image/png")})
    assert fake.status_code == 400
    noauth = client.post("/api/admin/uploads", files={"file": ("foto.png", io.BytesIO(PNG), "image/png")})
    assert noauth.status_code == 401
