def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_and_fetch_product(client):
    resp = client.post(
        "/products",
        json={"sku": "SKU-100", "name": "Hex bolt", "unit_price": 0.25, "reorder_level": 50},
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["sku"] == "SKU-100"

    fetched = client.get(f"/products/{created['id']}")
    assert fetched.status_code == 200
    body = fetched.json()
    assert body["name"] == "Hex bolt"
    assert body["on_hand"] == 0  # no movements yet


def test_duplicate_sku_is_rejected(client, product):
    resp = client.post("/products", json={"sku": product["sku"], "name": "Dupe"})
    assert resp.status_code == 409


def test_update_product(client, product):
    resp = client.patch(f"/products/{product['id']}", json={"reorder_level": 12})
    assert resp.status_code == 200
    assert resp.json()["reorder_level"] == 12


def test_delete_product(client, product):
    assert client.delete(f"/products/{product['id']}").status_code == 204
    assert client.get(f"/products/{product['id']}").status_code == 404


def test_search_and_filter(client):
    client.post("/products", json={"sku": "A-1", "name": "Anchor"})
    client.post("/products", json={"sku": "B-1", "name": "Bracket"})

    results = client.get("/products", params={"search": "anchor"}).json()
    assert len(results) == 1
    assert results[0]["name"] == "Anchor"


def test_missing_product_returns_404(client):
    assert client.get("/products/9999").status_code == 404
