from typing import Any

from google.cloud.firestore_v1 import SERVER_TIMESTAMP, AsyncClient

from app.firestore.collections import PAYMENTS
from app.models.payment import Payment
from app.repositories.base import FirestoreRepository


class PaymentRepository(FirestoreRepository):
    def __init__(self, client: AsyncClient) -> None:
        super().__init__(client, PAYMENTS)

    async def get(self, payment_id: str) -> Payment | None:
        data = await self.get_raw(payment_id)
        return Payment(**data) if data else None

    async def upsert_payment(self, payment: Payment) -> None:
        data = payment.model_dump(mode="json", exclude_none=True)
        await self.doc(payment.mercado_pago_payment_id).set(
            {**data, "created_at": SERVER_TIMESTAMP, "updated_at": SERVER_TIMESTAMP},
            merge=True,
        )

    async def update(self, payment_id: str, data: dict[str, Any]) -> None:
        await self.doc(payment_id).set({**data, "updated_at": SERVER_TIMESTAMP}, merge=True)

