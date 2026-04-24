def _move(client, product_id, kind, qty, note=None):
    return client.post(
        f"/products/{product_id}/movements",
        json={"kind": kind, "quantity": qty, "note": note},
    )


def test_receipt_increases_on_hand(client, product):
    assert _move(client, product["id"], "RECEIPT", 100).status_code == 201
    body = client.get(f"/products/{product['id']}").json()
    assert body["on_hand"] == 100


def test_shipment_decreases_on_hand(client, product):
    _move(client, product["id"], "RECEIPT", 100)
    _move(client, product["id"], "SHIPMENT", 30)
    assert client.get(f"/products/{product['id']}").json()["on_hand"] == 70


def test_cannot_ship_more_than_available(client, product):
    _move(client, product["id"], "RECEIPT", 10)
    resp = _move(client, product["id"], "SHIPMENT", 25)
    assert resp.status_code == 422
    assert "negative" in resp.json()["detail"].lower()
    # on-hand is unchanged after the rejected movement
    assert client.get(f"/products/{product['id']}").json()["on_hand"] == 10


def test_adjustment_recorded_as_signed(client, product):
    _move(client, product["id"], "RECEIPT", 50)
    _move(client, product["id"], "ADJUSTMENT", 5, note="found extra in bay 3")
    assert client.get(f"/products/{product['id']}").json()["on_hand"] == 55


def test_low_stock_report(client):
    p = client.post(
        "/products", json={"sku": "LOW-1", "name": "Scarce part", "reorder_level": 20}
    ).json()
    _move(client, p["id"], "RECEIPT", 15)  # below reorder level of 20

    report = client.get("/products/low-stock").json()
    skus = {row["sku"] for row in report}
    assert "LOW-1" in skus


def test_movement_history_newest_first(client, product):
    _move(client, product["id"], "RECEIPT", 10, note="first")
    _move(client, product["id"], "RECEIPT", 5, note="second")
    history = client.get(f"/products/{product['id']}/movements").json()
    assert len(history) == 2
    assert history[0]["note"] == "second"
