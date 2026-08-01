import hmac
import logging
from hashlib import sha256
from typing import Any

from app.config import Settings
from app.models.webhook_event import WebhookEvent
from app.repositories.webhook_repository import WebhookEventRepository, build_event_key
from app.services.mercado_pago_service import MercadoPagoService
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)


class InvalidWebhookSignature(Exception):
    pass


class WebhookService:
    def __init__(
        self,
        settings: Settings,
        webhook_repository: WebhookEventRepository,
        mercado_pago_service: MercadoPagoService,
        payment_service: PaymentService,
    ) -> None:
        self.settings = settings
        self.webhook_repository = webhook_repository
        self.mercado_pago_service = mercado_pago_service
        self.payment_service = payment_service

    def validate_signature(
        self,
        *,
        x_signature: str | None,
        x_request_id: str | None,
        data_id: str | None,
    ) -> None:
        """Validate Mercado Pago webhook signature.

        Mercado Pago signs a manifest composed as:
        id:{data.id};request-id:{x-request-id};ts:{ts};
        and sends x-signature values such as ts=...,v1=....
        """

        secret = self.settings.mp_webhook_secret.strip()
        if not secret:
            raise InvalidWebhookSignature("Webhook secret is not configured")
        if not x_signature:
            raise InvalidWebhookSignature("Missing x-signature header")
        parts = {
            key.strip(): value.strip()
            for item in x_signature.split(",")
            if "=" in item
            for key, value in [item.split("=", 1)]
        }
        ts = parts.get("ts")
        received_hash = parts.get("v1")
        if not ts or not received_hash:
            raise InvalidWebhookSignature("Malformed signature header")

        manifest_parts = []
        if data_id:
            normalized_data_id = data_id.lower() if data_id.isalnum() else data_id
            manifest_parts.append(f"id:{normalized_data_id};")
        if x_request_id:
            manifest_parts.append(f"request-id:{x_request_id};")
        manifest_parts.append(f"ts:{ts};")
        manifest = "".join(manifest_parts)
        expected_hash = hmac.new(
            secret.encode(),
            manifest.encode(),
            sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_hash, received_hash):
            raise InvalidWebhookSignature("Invalid webhook signature")

    async def process_webhook(
        self,
        *,
        payload: dict[str, Any],
        x_signature: str | None,
        x_request_id: str | None,
        query_data_id: str | None,
    ) -> str:
        resource_id = str(query_data_id or (payload.get("data") or {}).get("id") or "")
        self.validate_signature(
            x_signature=x_signature,
            x_request_id=x_request_id,
            data_id=query_data_id,
        )
        event_key = build_event_key(
            str(payload.get("id") or x_request_id), payload.get("action"), resource_id
        )
        existing = await self.webhook_repository.get(event_key)
        if existing and existing.processing_status == "completed":
            logger.info("Duplicate webhook event_key=%s", event_key)
            await self.webhook_repository.update(event_key, {"attempts": existing.attempts + 1})
            return event_key
        await self.webhook_repository.create_received(
            WebhookEvent(
                event_key=event_key,
                mercado_pago_event_id=str(payload.get("id")) if payload.get("id") else None,
                event_type=payload.get("type"),
                action=payload.get("action"),
                resource_id=resource_id,
                request_id=x_request_id,
                signature_present=bool(x_signature),
                processing_status="processing",
                attempts=(existing.attempts + 1) if existing else 1,
                payload=payload,
            )
        )
        try:
            raw_payment = await self.mercado_pago_service.get_payment(resource_id)
            await self.payment_service.reconcile_payment(raw_payment)
        except Exception as exc:
            await self.webhook_repository.update(
                event_key,
                {"processing_status": "failed", "last_error": str(exc)[:500]},
            )
            raise
        await self.webhook_repository.update(event_key, {"processing_status": "completed"})
        return event_key
