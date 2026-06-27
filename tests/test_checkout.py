import pytest

from app.config import Settings
from app.schemas.checkout import CheckoutPreferenceRequest
from app.services.mercado_pago_service import MercadoPagoAPIError
from app.services.order_service import OrderService
from tests.conftest import FakeMP, MemoryOrderRepository


@pytest.mark.asyncio
async def test_create_order_and_preference() -> None:
    repo = MemoryOrderRepository()
    service = OrderService(
        repo,
        FakeMP(),
        Settings(mp_access_token="token", mp_webhook_secret="secret"),
    )
    result = await service.create_checkout_preference(CheckoutPreferenceRequest())
    order = await repo.get(result.order_id)
    assert result.preference_id == "pref_123"
    assert order.external_reference == result.order_id
    assert order.internal_status == "preference_created"
    assert order.total_amount_minor == 150000


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
