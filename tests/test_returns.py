from fastapi.testclient import TestClient

from app.main import app


def test_back_url_without_payment_id() -> None:
    with TestClient(app) as client:
        response = client.get("/checkout/success")
    assert response.status_code == 400
    assert "No se recibió payment_id" in response.text
    assert "Tienda demo" in response.text
    assert "/static/checkout-result.css" in response.text
