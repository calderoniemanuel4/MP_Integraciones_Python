import pytest

from app.config import Settings
from app.schemas.checkout import CheckoutPreferenceRequest
from app.services.mercado_pago_service import MercadoPagoAPIError
from app.services.order_service import OrderService
from tests.conftest import FakeMP, MemoryOrderRepository


@pytest.mark.asyncio
async def test_create_order_and_preference() -> None:
    repo = MemoryOrderRepository()
    mercado_pago = FakeMP()
    service = OrderService(
        repo,
        mercado_pago,
        Settings(mp_access_token="token", mp_webhook_secret="secret"),
    )
    result = await service.create_checkout_preference(CheckoutPreferenceRequest())
    order = await repo.get(result.order_id)
    assert result.preference_id == "pref_123"
    assert result.checkout_url.startswith("https://www.mercadopago.com/")
    assert order.external_reference == result.order_id
    assert order.title == "Tienda Móvil"
    assert order.internal_status == "preference_created"
    assert order.total_amount_minor == 150000
    assert mercado_pago.preference_payload is not None
    assert mercado_pago.preference_payload["items"] == [
        {
            "id": "1001",
            "title": "Tienda Móvil",
            "description": "Dispositivo de tienda móvil de comercio electrónico",
            "picture_url": (
                "https://mp-pagos-api.fastapicloud.dev/static/product-speaker.jpg"
            ),
            "quantity": 1,
            "unit_price": 1500.0,
            "currency_id": "ARS",
        }
    ]
    assert mercado_pago.preference_payload["payment_methods"] == {
        "excluded_payment_methods": [{"id": "visa"}],
        "installments": 6,
    }


@pytest.mark.asyncio
async def test_sandbox_mode_returns_sandbox_checkout_url() -> None:
    repo = MemoryOrderRepository()
    service = OrderService(
        repo,
        FakeMP(),
        Settings(
            mp_access_token="token",
            mp_webhook_secret="secret",
            mp_checkout_mode="sandbox",
        ),
    )

    result = await service.create_checkout_preference(CheckoutPreferenceRequest())

    assert result.checkout_url.startswith("https://sandbox.mercadopago.com/")
    order = await repo.get(result.order_id)
    assert order.checkout_url == result.checkout_url


@pytest.mark.asyncio
async def test_legacy_product_code_uses_current_catalog_product() -> None:
    repo = MemoryOrderRepository()
    mercado_pago = FakeMP()
    service = OrderService(
        repo,
        mercado_pago,
        Settings(mp_access_token="token", mp_webhook_secret="secret"),
    )

    await service.create_checkout_preference(
        CheckoutPreferenceRequest(product_code="test-product")
    )

    assert mercado_pago.preference_payload is not None
    assert mercado_pago.preference_payload["items"][0]["id"] == "1001"


@pytest.mark.asyncio
async def test_preference_error_marks_order_error() -> None:
    repo = MemoryOrderRepository()
    service = OrderService(
        repo,
        FakeMP(preference_error=MercadoPagoAPIError("boom")),
        Settings(mp_access_token="token", mp_webhook_secret="secret"),
    )
    with pytest.raises(MercadoPagoAPIError):
        await service.create_checkout_preference(CheckoutPreferenceRequest())
    [order] = repo.rows.values()
    assert order.internal_status == "error"
