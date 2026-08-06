from fastapi.testclient import TestClient

from app.dependencies import webhook_service_dep
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
    assert "Tienda Móvil" in response.text
    assert "window.location.origin" in response.text
    assert "/static/product-speaker.jpg" in response.text


def test_checkout_product_image_is_served() -> None:
    with TestClient(app) as client:
        response = client.get("/static/product-speaker.jpg")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


def test_webhook_rejects_malformed_json_as_bad_request() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/webhooks/mercadopago?data.id=123456&type=payment",
            content='{"data": {"id": "123456"}} trailing-data',
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "Malformed JSON payload"}


def test_webhook_uses_preserved_signature_request_id() -> None:
    class CapturingWebhookService:
        request_id: str | None = None

        async def process_webhook(self, **kwargs) -> str:
            self.request_id = kwargs["x_request_id"]
            return "event-1"

    service = CapturingWebhookService()
    app.dependency_overrides[webhook_service_dep] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.post(
                "/webhooks/mercadopago?data.id=123456&type=payment",
                json={"data": {"id": "123456"}},
                headers={
                    "x-signature": "ts=1,v1=abc",
                    "x-request-id": "proxy-request-id",
                    "x-mp-signature-request-id": "signed-request-id",
                },
            )
    finally:
        app.dependency_overrides.pop(webhook_service_dep, None)

    assert response.status_code == 200
    assert service.request_id == "signed-request-id"
