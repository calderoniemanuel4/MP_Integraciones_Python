from typing import Any

from google.cloud.firestore_v1 import SERVER_TIMESTAMP, AsyncClient


class FirestoreRepository:
    def __init__(self, client: AsyncClient, collection_name: str) -> None:
        self.client = client
        self.collection_name = collection_name

    def collection(self) -> Any:
        return self.client.collection(self.collection_name)

    def doc(self, doc_id: str) -> Any:
        return self.collection().document(doc_id)

    async def get_raw(self, doc_id: str) -> dict[str, Any] | None:
        snapshot = await self.doc(doc_id).get()
        if not snapshot.exists:
            return None
        return snapshot.to_dict()

    async def upsert(self, doc_id: str, data: dict[str, Any]) -> None:
        await self.doc(doc_id).set({**data, "updated_at": SERVER_TIMESTAMP}, merge=True)

    async def list_by_field(
        self, field: str, value: Any, *, order_by: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        query = self.collection().where(field, "==", value)
        if order_by:
            query = query.order_by(order_by)
        docs = query.limit(limit).stream()
        return [doc.to_dict() async for doc in docs]

