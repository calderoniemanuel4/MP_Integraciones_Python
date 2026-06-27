from typing import Any

from google.cloud.firestore_v1 import SERVER_TIMESTAMP, AsyncClient

from app.firestore.collections import ORDERS
from app.models.order import Order
from app.repositories.base import FirestoreRepository


class OrderRepository(FirestoreRepository):
    def __init__(self, client: AsyncClient) -> None:
        super().__init__(client, ORDERS)

    async def create(self, order: Order) -> None:
        data = order.model_dump(mode="json", exclude_none=True)
        await self.doc(order.order_id).create(
            {**data, "created_at": SERVER_TIMESTAMP, "updated_at": SERVER_TIMESTAMP}
        )

    async def get(self, order_id: str) -> Order | None:
        data = await self.get_raw(order_id)
        return Order(**data) if data else None

    async def update(self, order_id: str, data: dict[str, Any]) -> None:
        await self.doc(order_id).set({**data, "updated_at": SERVER_TIMESTAMP}, merge=True)

    async def list_by_status(self, status: str, limit: int = 50) -> list[Order]:
        rows = await self.list_by_field(
            "internal_status", status, order_by="created_at", limit=limit
        )
        return [Order(**row) for row in rows]
