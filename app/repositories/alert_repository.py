from google.cloud.firestore_v1 import SERVER_TIMESTAMP, AsyncClient

from app.firestore.collections import PAYMENT_ALERTS
from app.models.payment_alert import PaymentAlert
from app.repositories.base import FirestoreRepository
from app.repositories.webhook_repository import normalize_doc_id


def build_alert_id(alert_type: str, order_id: str | None, payment_id: str | None) -> str:
    return normalize_doc_id(f"{alert_type}_{order_id or 'no_order'}_{payment_id or 'no_payment'}")


class PaymentAlertRepository(FirestoreRepository):
    def __init__(self, client: AsyncClient) -> None:
        super().__init__(client, PAYMENT_ALERTS)

    async def get(self, alert_id: str) -> PaymentAlert | None:
        data = await self.get_raw(alert_id)
        return PaymentAlert(**data) if data else None

    async def upsert_alert(self, alert: PaymentAlert) -> None:
        data = alert.model_dump(mode="json", exclude_none=True)
        await self.doc(alert.alert_id).set(
            {**data, "created_at": SERVER_TIMESTAMP, "updated_at": SERVER_TIMESTAMP},
            merge=True,
        )

    async def list_unresolved(self, limit: int = 50) -> list[PaymentAlert]:
        return [
            PaymentAlert(**row)
            for row in await self.list_by_field(
                "resolved", False, order_by="created_at", limit=limit
            )
        ]
