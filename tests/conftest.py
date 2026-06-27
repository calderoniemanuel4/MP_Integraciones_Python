import os

import pytest

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "mp-checkout-pro-test")
os.environ.setdefault("MP_WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")


def pytest_configure(config: pytest.Config) -> None:
    return None


@pytest.fixture
def require_firestore_emulator() -> None:
    if not os.environ.get("FIRESTORE_EMULATOR_HOST"):
        pytest.fail("FIRESTORE_EMULATOR_HOST is required for tests that write to Firestore")


class MemoryOrderRepository:
    def __init__(self) -> None:
        self.rows = {}

    async def create(self, order) -> None:
        if order.order_id in self.rows:
            raise ValueError("already exists")
        self.rows[order.order_id] = order

    async def get(self, order_id: str):
        return self.rows.get(order_id)

    async def update(self, order_id: str, data: dict) -> None:
        order = self.rows[order_id]
        self.rows[order_id] = order.model_copy(update=data)


class MemoryPaymentRepository:
    def __init__(self) -> None:
        self.rows = {}

    async def get(self, payment_id: str):
        return self.rows.get(payment_id)

    async def upsert_payment(self, payment) -> None:
        self.rows[payment.mercado_pago_payment_id] = payment


class MemoryAlertRepository:
    def __init__(self) -> None:
        self.rows = {}

    async def upsert_alert(self, alert) -> None:
        self.rows[alert.alert_id] = alert

    async def list_unresolved(self, limit: int = 50):
        return [a for a in self.rows.values() if not a.resolved][:limit]


class MemoryWebhookRepository:
    def __init__(self) -> None:
        self.rows = {}

    async def get(self, event_key: str):
        return self.rows.get(event_key)

    async def create_received(self, event) -> None:
        self.rows[event.event_key] = event

    async def update(self, event_key: str, data: dict) -> None:
        self.rows[event_key] = self.rows[event_key].model_copy(update=data)


class FakeMP:
    def __init__(
        self,
        payment: dict | None = None,
        preference_error: Exception | None = None,
    ) -> None:
        self.payment = payment
        self.preference_error = preference_error

    async def create_preference(self, payload: dict) -> dict:
        if self.preference_error:
            raise self.preference_error
        return {
            "id": "pref_123",
            "init_point": "https://www.mercadopago.com/checkout/v1/redirect?pref_id=pref_123",
            "sandbox_init_point": (
                "https://sandbox.mercadopago.com/checkout/v1/redirect?pref_id=pref_123"
            ),
        }

    async def get_payment(self, payment_id: str) -> dict:
        return self.payment or {
            "id": payment_id,
            "external_reference": "order-1",
            "status": "approved",
            "status_detail": "accredited",
            "transaction_amount": "1500.00",
            "currency_id": "ARS",
        }
