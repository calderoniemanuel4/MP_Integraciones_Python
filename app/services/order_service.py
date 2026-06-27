import logging
from decimal import Decimal
from uuid import uuid4

from app.config import Settings
from app.models.order import Order
from app.repositories.order_repository import OrderRepository
from app.schemas.checkout import CheckoutPreferenceRequest, CheckoutPreferenceResponse, ProductQuote
from app.services.mercado_pago_service import MercadoPagoAPIError, MercadoPagoService
from app.services.money_service import MoneyService

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        mercado_pago_service: MercadoPagoService,
        settings: Settings,
    ) -> None:
        self.order_repository = order_repository
        self.mercado_pago_service = mercado_pago_service
        self.settings = settings

    async def create_checkout_preference(
        self, request: CheckoutPreferenceRequest
    ) -> CheckoutPreferenceResponse:
        quote = self._quote_product(request.product_code)
        order_id = str(uuid4())
        unit_price_minor = MoneyService.to_minor_units(quote.unit_price, quote.currency_id)
        total_amount_minor = unit_price_minor * request.quantity
        order = Order(
            order_id=order_id,
            external_reference=order_id,
            title=quote.title,
            quantity=request.quantity,
            unit_price_minor=unit_price_minor,
            total_amount_minor=total_amount_minor,
            currency_id=quote.currency_id,
        )
        await self.order_repository.create(order)
        payload = {
            "items": [
                {
                    "title": quote.title,
                    "quantity": request.quantity,
                    "unit_price": float(quote.unit_price),
                    "currency_id": quote.currency_id,
                }
            ],
            "external_reference": order_id,
            "back_urls": {
                "success": str(self.settings.mp_success_url),
                "failure": str(self.settings.mp_failure_url),
                "pending": str(self.settings.mp_pending_url),
            },
            "auto_return": "approved",
            "notification_url": str(self.settings.mp_webhook_url),
            "metadata": {"order_id": order_id},
        }
        try:
            preference = await self.mercado_pago_service.create_preference(payload)
        except MercadoPagoAPIError as exc:
            await self.order_repository.update(order_id, {"internal_status": "error"})
            logger.exception("Preference creation failed order_id=%s", order_id)
            raise exc
        checkout_url = preference.get("init_point") or preference.get("sandbox_init_point")
        await self.order_repository.update(
            order_id,
            {
                "preference_id": preference["id"],
                "checkout_url": checkout_url,
                "sandbox_checkout_url": preference.get("sandbox_init_point"),
                "internal_status": "preference_created",
            },
        )
        logger.info("Preference created order_id=%s preference_id=%s", order_id, preference["id"])
        return CheckoutPreferenceResponse(
            order_id=order_id,
            external_reference=order_id,
            preference_id=preference["id"],
            checkout_url=checkout_url,
            sandbox_checkout_url=preference.get("sandbox_init_point"),
        )

    def _quote_product(self, product_code: str) -> ProductQuote:
        # Price is intentionally determined server-side. Browser values are ignored.
        return ProductQuote(
            title="Producto de prueba",
            unit_price=Decimal("1500.00"),
            currency_id="ARS",
        )
