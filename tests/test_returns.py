import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.dependencies import mercado_pago_service_dep, payment_service_dep
from app.main import app
from app.models.order import Order
from app.routers.returns import normalize_mp_query_value, render_result
from app.services.payment_service import PaymentService
from tests.conftest import (
    FakeMP,
    MemoryAlertRepository,
    MemoryOrderRepository,
    MemoryPaymentRepository,
)


@pytest.fixture
def return_dependencies():
    mercado_pago = FakeMP()
    orders = MemoryOrderRepository()
    payment_service = PaymentService(
        orders,
        MemoryPaymentRepository(),
        MemoryAlertRepository(),
    )
    app.dependency_overrides[mercado_pago_service_dep] = lambda: mercado_pago
    app.dependency_overrides[payment_service_dep] = lambda: payment_service
    try:
        yield mercado_pago, payment_service, orders
    finally:
        app.dependency_overrides.pop(mercado_pago_service_dep, None)
        app.dependency_overrides.pop(payment_service_dep, None)


def test_normalize_mp_query_value() -> None:
    assert normalize_mp_query_value(None) is None
    assert normalize_mp_query_value("") is None
    assert normalize_mp_query_value("   ") is None
    assert normalize_mp_query_value("null") is None
    assert normalize_mp_query_value("None") is None
    assert normalize_mp_query_value(" payment-1 ") == "payment-1"


def test_failure_with_literal_null_payment_id(return_dependencies) -> None:
    mercado_pago, _, _ = return_dependencies

    with TestClient(app) as client:
        response = client.get("/checkout/failure?payment_id=null")

    assert response.status_code == 200
    assert "No se generó un pago" in response.text
    assert mercado_pago.requested_payment_ids == []


def test_failure_without_payment_id(return_dependencies) -> None:
    mercado_pago, _, _ = return_dependencies

    with TestClient(app) as client:
        response = client.get("/checkout/failure")

    assert response.status_code == 200
    assert "No se generó un pago para consultar" in response.text
    assert mercado_pago.requested_payment_ids == []


def test_failure_with_valid_external_reference_marks_order_cancelled(
    return_dependencies,
) -> None:
    _, _, orders = return_dependencies
    orders.rows["order-1"] = Order(
        order_id="order-1",
        external_reference="order-1",
        title="Tienda Móvil",
        quantity=1,
        unit_price_minor=150000,
        total_amount_minor=150000,
        currency_id="ARS",
        internal_status="preference_created",
    )

    with TestClient(app) as client:
        response = client.get(
            "/checkout/failure?payment_id=null&external_reference=%20order-1%20"
        )

    assert response.status_code == 200
    assert orders.rows["order-1"].internal_status == "cancelled"


def test_success_with_literal_null_payment_id(return_dependencies) -> None:
    mercado_pago, _, _ = return_dependencies

    with TestClient(app) as client:
        response = client.get(
            "/checkout/success?payment_id=null&status=None"
            "&external_reference=null&preference_id=%20%20"
        )

    assert response.status_code == 200
    assert "Sin pago" in response.text
    assert mercado_pago.requested_payment_ids == []


@pytest.mark.asyncio
async def test_render_result_does_not_call_mp_without_payment_id(
    return_dependencies,
) -> None:
    mercado_pago, payment_service, _ = return_dependencies
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/checkout/failure",
            "headers": [],
            "query_string": b"",
        }
    )

    response = await render_result(
        request,
        "failure",
        None,
        mercado_pago,
        payment_service,
    )

    assert response.status_code == 200
    assert mercado_pago.requested_payment_ids == []
