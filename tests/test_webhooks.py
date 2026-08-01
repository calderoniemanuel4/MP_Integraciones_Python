import asyncio
import hmac
from hashlib import sha256

import pytest

from app.config import Settings
from app.models.order import Order
from app.repositories.webhook_repository import build_event_key
from app.services.payment_service import PaymentService
from app.services.webhook_service import InvalidWebhookSignature, WebhookService
from tests.conftest import (
    FakeMP,
    MemoryAlertRepository,
    MemoryOrderRepository,
    MemoryPaymentRepository,
    MemoryWebhookRepository,
)


def signature(
    secret: str,
    data_id: str | None,
    request_id: str | None,
    ts: str = "1",
) -> str:
    manifest = ""
    if data_id:
        manifest += f"id:{data_id};"
    if request_id:
        manifest += f"request-id:{request_id};"
    manifest += f"ts:{ts};"
    digest = hmac.new(secret.encode(), manifest.encode(), sha256).hexdigest()
    return f"ts={ts},v1={digest}"


@pytest.mark.asyncio
async def test_invalid_webhook_signature() -> None:
    service = WebhookService(
        Settings(mp_webhook_secret="secret"),
        MemoryWebhookRepository(),
        FakeMP(),
        PaymentService(MemoryOrderRepository(), MemoryPaymentRepository(), MemoryAlertRepository()),
    )
    with pytest.raises(InvalidWebhookSignature):
        service.validate_signature(x_signature="ts=1,v1=bad", x_request_id="req", data_id="123")


def test_signature_accepts_whitespace_and_normalizes_alphanumeric_id() -> None:
    service = WebhookService(
        Settings(mp_webhook_secret="secret"),
        MemoryWebhookRepository(),
        FakeMP(),
        PaymentService(MemoryOrderRepository(), MemoryPaymentRepository(), MemoryAlertRepository()),
    )
    signed = signature("secret", "abc123", "req").replace(",", ", ")

    service.validate_signature(
        x_signature=signed,
        x_request_id="req",
        data_id="ABC123",
    )


def test_signature_omits_components_missing_from_request() -> None:
    service = WebhookService(
        Settings(mp_webhook_secret="secret"),
        MemoryWebhookRepository(),
        FakeMP(),
        PaymentService(MemoryOrderRepository(), MemoryPaymentRepository(), MemoryAlertRepository()),
    )

    service.validate_signature(
        x_signature=signature("secret", None, None),
        x_request_id=None,
        data_id=None,
    )


@pytest.mark.asyncio
async def test_valid_webhook_and_duplicate() -> None:
    orders = MemoryOrderRepository()
    await orders.create(
        Order(
            order_id="order-1",
            external_reference="order-1",
            title="Producto",
            quantity=1,
            unit_price_minor=150000,
            total_amount_minor=150000,
            currency_id="ARS",
            internal_status="preference_created",
        )
    )
    payments = MemoryPaymentRepository()
    alerts = MemoryAlertRepository()
    webhooks = MemoryWebhookRepository()
    service = WebhookService(
        Settings(mp_webhook_secret="secret"),
        webhooks,
        FakeMP(),
        PaymentService(orders, payments, alerts),
    )
    payload = {"id": "evt", "type": "payment", "action": "payment.updated", "data": {"id": "123"}}
    sig = signature("secret", "123", "req")
    event_key = await service.process_webhook(
        payload=payload, x_signature=sig, x_request_id="req", query_data_id="123"
    )
    duplicate = await service.process_webhook(
        payload=payload, x_signature=sig, x_request_id="req", query_data_id="123"
    )
    assert event_key == duplicate == build_event_key("evt", "payment.updated", "123")
    assert (await orders.get("order-1")).internal_status == "approved"
    assert len(payments.rows) == 1


@pytest.mark.asyncio
async def test_two_simultaneous_duplicate_webhooks() -> None:
    orders = MemoryOrderRepository()
    await orders.create(
        Order(
            order_id="order-1",
            external_reference="order-1",
            title="Producto",
            quantity=1,
            unit_price_minor=150000,
            total_amount_minor=150000,
            currency_id="ARS",
            internal_status="preference_created",
        )
    )
    webhooks = MemoryWebhookRepository()
    service = WebhookService(
        Settings(mp_webhook_secret="secret"),
        webhooks,
        FakeMP(),
        PaymentService(orders, MemoryPaymentRepository(), MemoryAlertRepository()),
    )
    payload = {"id": "evt", "type": "payment", "action": "payment.updated", "data": {"id": "123"}}
    sig = signature("secret", "123", "req")
    results = await asyncio.gather(
        service.process_webhook(
            payload=payload, x_signature=sig, x_request_id="req", query_data_id="123"
        ),
        service.process_webhook(
            payload=payload, x_signature=sig, x_request_id="req", query_data_id="123"
        ),
    )
    assert results == [build_event_key("evt", "payment.updated", "123")] * 2
    assert len(webhooks.rows) == 1
