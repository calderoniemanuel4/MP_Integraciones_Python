import logging
from typing import Any

from app.models.payment import Payment
from app.models.payment_alert import PaymentAlert
from app.repositories.alert_repository import PaymentAlertRepository, build_alert_id
from app.repositories.order_repository import OrderRepository
from app.repositories.payment_repository import PaymentRepository
from app.services.money_service import MoneyService
from app.services.state_machine import can_transition, mp_status_to_internal

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(
        self,
        order_repository: OrderRepository,
        payment_repository: PaymentRepository,
        alert_repository: PaymentAlertRepository,
    ) -> None:
        self.order_repository = order_repository
        self.payment_repository = payment_repository
        self.alert_repository = alert_repository

    async def reconcile_payment(self, raw_payment: dict[str, Any]) -> Payment:
        payment = self.payment_from_mp(raw_payment)
        await self.payment_repository.upsert_payment(payment)
        if not payment.external_reference:
            await self._alert(
                "payment_without_external_reference",
                None,
                payment.mercado_pago_payment_id,
                None,
                None,
            )
            return payment

        order = await self.order_repository.get(payment.external_reference)
        if order is None:
            await self._alert(
                "order_not_found",
                payment.external_reference,
                payment.mercado_pago_payment_id,
                "existing order",
                "not found",
            )
            return payment

        new_internal_status = mp_status_to_internal(payment.status)
        updates: dict[str, Any] = {
            "mp_payment_status": payment.status,
            "mp_payment_status_detail": payment.status_detail,
            "mercado_pago_payment_id": payment.mercado_pago_payment_id,
            "live_mode": payment.live_mode,
        }
        if payment.transaction_amount_minor != order.total_amount_minor:
            updates["internal_status"] = "manual_review"
            await self._alert(
                "amount_mismatch",
                order.order_id,
                payment.mercado_pago_payment_id,
                str(order.total_amount_minor),
                str(payment.transaction_amount_minor),
            )
        elif payment.currency_id != order.currency_id:
            updates["internal_status"] = "manual_review"
            await self._alert(
                "currency_mismatch",
                order.order_id,
                payment.mercado_pago_payment_id,
                order.currency_id,
                payment.currency_id,
            )
        elif can_transition(order.internal_status, new_internal_status):
            updates["internal_status"] = new_internal_status
        else:
            updates["internal_status"] = "manual_review"
            await self._alert(
                "invalid_state_transition",
                order.order_id,
                payment.mercado_pago_payment_id,
                order.internal_status,
                new_internal_status,
            )
        await self.order_repository.update(order.order_id, updates)
        logger.info(
            "Payment reconciled order_id=%s payment_id=%s status=%s",
            order.order_id,
            payment.mercado_pago_payment_id,
            payment.status,
        )
        return payment

    def payment_from_mp(self, raw_payment: dict[str, Any]) -> Payment:
        currency_id = raw_payment.get("currency_id")
        amount_minor = None
        if raw_payment.get("transaction_amount") is not None and currency_id:
            amount_minor = MoneyService.decimal_from_mp_amount(
                raw_payment["transaction_amount"], currency_id
            )
        payment_id = str(raw_payment["id"])
        external_reference = raw_payment.get("external_reference")
        metadata_order_id = (raw_payment.get("metadata") or {}).get("order_id")
        return Payment(
            mercado_pago_payment_id=payment_id,
            order_id=external_reference or metadata_order_id,
            external_reference=external_reference,
            status=raw_payment.get("status") or "unknown",
            status_detail=raw_payment.get("status_detail"),
            transaction_amount_minor=amount_minor,
            currency_id=currency_id,
            payment_type_id=raw_payment.get("payment_type_id"),
            payment_method_id=raw_payment.get("payment_method_id"),
            installments=raw_payment.get("installments"),
            live_mode=raw_payment.get("live_mode"),
            date_created=raw_payment.get("date_created"),
            date_approved=raw_payment.get("date_approved"),
            date_last_updated=raw_payment.get("date_last_updated"),
            raw_payment=raw_payment,
        )

    async def _alert(
        self,
        alert_type: str,
        order_id: str | None,
        payment_id: str | None,
        expected: str | None,
        received: str | None,
    ) -> None:
        alert_id = build_alert_id(alert_type, order_id, payment_id)
        await self.alert_repository.upsert_alert(
            PaymentAlert(
                alert_id=alert_id,
                type=alert_type,  # type: ignore[arg-type]
                severity="high" if alert_type.endswith("mismatch") else "medium",
                order_id=order_id,
                payment_id=payment_id,
                expected_value=expected,
                received_value=received,
                message=f"{alert_type}: expected={expected} received={received}",
            )
        )
