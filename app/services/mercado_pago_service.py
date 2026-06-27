import logging
from typing import Any

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


class MercadoPagoAPIError(Exception):
    """Raised when Mercado Pago returns an error or an invalid response."""


class MercadoPagoService:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self.client = client or httpx.AsyncClient(
            base_url=settings.mp_api_base_url,
            timeout=settings.request_timeout_seconds,
            headers={"Authorization": f"Bearer {settings.mp_access_token}"},
        )

    async def create_preference(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self.client.post("/checkout/preferences", json=payload)
        except httpx.HTTPError as exc:
            logger.exception("Mercado Pago preference request failed")
            raise MercadoPagoAPIError("Mercado Pago preference request failed") from exc
        if response.status_code >= 400:
            logger.error(
                "Mercado Pago preference error status=%s body=%s",
                response.status_code,
                _safe_body(response),
            )
            raise MercadoPagoAPIError(f"Mercado Pago preference error {response.status_code}")
        data = response.json()
        if "id" not in data or ("init_point" not in data and "sandbox_init_point" not in data):
            raise MercadoPagoAPIError("Mercado Pago preference response is missing required fields")
        return data

    async def get_payment(self, payment_id: str) -> dict[str, Any]:
        try:
            response = await self.client.get(f"/v1/payments/{payment_id}")
        except httpx.HTTPError as exc:
            logger.exception("Mercado Pago payment request failed payment_id=%s", payment_id)
            raise MercadoPagoAPIError("Mercado Pago payment request failed") from exc
        if response.status_code >= 400:
            logger.error(
                "Mercado Pago payment error status=%s payment_id=%s",
                response.status_code,
                payment_id,
            )
            raise MercadoPagoAPIError(f"Mercado Pago payment error {response.status_code}")
        return response.json()


def _safe_body(response: httpx.Response) -> str:
    return response.text[:500].replace("Bearer ", "Bearer ***")
