import re
from typing import Any

from google.cloud.firestore_v1 import SERVER_TIMESTAMP, AsyncClient

from app.firestore.collections import WEBHOOK_EVENTS
from app.models.webhook_event import WebhookEvent
from app.repositories.base import FirestoreRepository


def normalize_doc_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")[:1200] or "unknown"


def build_event_key(event_id: str | None, action: str | None, resource_id: str | None) -> str:
    raw_key = (
        f"{event_id or 'no_event_id'}_"
        f"{action or 'no_action'}_"
        f"{resource_id or 'no_resource'}"
    )
    return normalize_doc_id(raw_key)


class WebhookEventRepository(FirestoreRepository):
    def __init__(self, client: AsyncClient) -> None:
        super().__init__(client, WEBHOOK_EVENTS)

    async def get(self, event_key: str) -> WebhookEvent | None:
        data = await self.get_raw(event_key)
        return WebhookEvent(**data) if data else None

    async def create_received(self, event: WebhookEvent) -> None:
        await self.doc(event.event_key).set(
            {
                **event.model_dump(mode="json", exclude_none=True),
                "received_at": SERVER_TIMESTAMP,
                "updated_at": SERVER_TIMESTAMP,
            },
            merge=True,
        )

    async def update(self, event_key: str, data: dict[str, Any]) -> None:
        await self.doc(event_key).set({**data, "updated_at": SERVER_TIMESTAMP}, merge=True)
