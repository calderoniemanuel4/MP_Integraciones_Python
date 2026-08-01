from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "mp-checkout-pro-firestore"}


def test_frontend_is_served_by_the_api() -> None:
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "Producto de prueba" in response.text
    assert "window.location.origin" in response.text
