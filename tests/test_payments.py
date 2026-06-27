import pytest

from app.models.order import Order
from app.services.payment_service import PaymentService
from tests.conftest import MemoryAlertRepository, MemoryOrderRepository, MemoryPaymentRepository


async def make_service(status: str = "preference_created"):
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
            internal_status=status,
        )
    )
    payments = MemoryPaymentRepository()
    alerts = MemoryAlertRepository()
    return PaymentService(orders, payments, alerts), orders, payments, alerts


@pytest.mark.asyncio
async def test_amount_mismatch_creates_alert() -> None:
    service, orders, _, alerts = await make_service()
    await service.reconcile_payment(
        {
            "id": "p1",
            "external_reference": "order-1",
            "status": "approved",
            "transaction_amount": "100.00",
            "currency_id": "ARS",
        }
    )
    assert (await orders.get("order-1")).internal_status == "manual_review"
    assert "amount_mismatch_order-1_p1" in alerts.rows


@pytest.mark.asyncio
async def test_amount_alert_is_idempotent() -> None:
    service, _, _, alerts = await make_service()
    raw = {
        "id": "p1",
        "external_reference": "order-1",
        "status": "approved",
        "transaction_amount": "100.00",
        "currency_id": "ARS",
    }
    await service.reconcile_payment(raw)
    await service.reconcile_payment(raw)
    assert list(alerts.rows) == ["amount_mismatch_order-1_p1"]


@pytest.mark.asyncio
async def test_currency_mismatch_creates_alert() -> None:
    service, orders, _, alerts = await make_service()
    await service.reconcile_payment(
        {
            "id": "p1",
            "external_reference": "order-1",
            "status": "approved",
            "transaction_amount": "1500.00",
            "currency_id": "USD",
        }
    )
    assert (await orders.get("order-1")).internal_status == "manual_review"
    assert "currency_mismatch_order-1_p1" in alerts.rows


@pytest.mark.asyncio
async def test_approved_payment_updates_order() -> None:
    service, orders, payments, alerts = await make_service()
    await service.reconcile_payment(
        {
            "id": "p1",
            "external_reference": "order-1",
            "status": "approved",
            "status_detail": "accredited",
            "transaction_amount": "1500.00",
            "currency_id": "ARS",
        }
    )
    assert (await orders.get("order-1")).internal_status == "approved"
    assert (await payments.get("p1")).status == "approved"
    assert alerts.rows == {}


@pytest.mark.asyncio
async def test_pending_payment_updates_order() -> None:
    service, orders, _, _ = await make_service()
    await service.reconcile_payment(
        {
            "id": "p1",
            "external_reference": "order-1",
            "status": "pending",
            "transaction_amount": "1500.00",
            "currency_id": "ARS",
        }
    )
    assert (await orders.get("order-1")).internal_status == "pending"


@pytest.mark.asyncio
async def test_rejected_payment_updates_order() -> None:
    service, orders, _, _ = await make_service()
    await service.reconcile_payment(
        {
            "id": "p1",
            "external_reference": "order-1",
            "status": "rejected",
            "transaction_amount": "1500.00",
            "currency_id": "ARS",
        }
    )
    assert (await orders.get("order-1")).internal_status == "rejected"


@pytest.mark.asyncio
async def test_refunded_payment_updates_approved_order() -> None:
    service, orders, _, _ = await make_service(status="approved")
    await service.reconcile_payment(
        {
            "id": "p1",
            "external_reference": "order-1",
            "status": "refunded",
            "transaction_amount": "1500.00",
            "currency_id": "ARS",
        }
    )
    assert (await orders.get("order-1")).internal_status == "refunded"


@pytest.mark.asyncio
async def test_order_not_found_creates_alert() -> None:
    service, _, _, alerts = await make_service()
    await service.reconcile_payment(
        {
            "id": "p1",
            "external_reference": "missing-order",
            "status": "approved",
            "transaction_amount": "1500.00",
            "currency_id": "ARS",
        }
    )
    assert "order_not_found_missing-order_p1" in alerts.rows


@pytest.mark.asyncio
async def test_payment_without_external_reference_creates_alert() -> None:
    service, _, payments, alerts = await make_service()
    await service.reconcile_payment(
        {
            "id": "p1",
            "status": "approved",
            "transaction_amount": "1500.00",
            "currency_id": "ARS",
        }
    )
    assert (await payments.get("p1")).external_reference is None
    assert "payment_without_external_reference_no_order_p1" in alerts.rows


@pytest.mark.asyncio
async def test_invalid_transition_creates_alert() -> None:
    service, orders, _, alerts = await make_service(status="approved")
    await service.reconcile_payment(
        {
            "id": "p1",
            "external_reference": "order-1",
            "status": "pending",
            "transaction_amount": "1500.00",
            "currency_id": "ARS",
        }
    )
    assert (await orders.get("order-1")).internal_status == "manual_review"
    assert "invalid_state_transition_order-1_p1" in alerts.rows
