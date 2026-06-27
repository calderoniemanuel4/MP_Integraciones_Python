from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

WebhookProcessingStatus = Literal["received", "processing", "completed", "ignored", "failed"]


class WebhookEvent(BaseModel):
    event_key: str
    mercado_pago_event_id: str | None = None
    event_type: str | None = None
    action: str | None = None
    resource_id: str | None = None
    request_id: str | None = None
    signature_present: bool = False
    processing_status: WebhookProcessingStatus = "received"
    attempts: int = 0
    payload: dict[str, Any] = Field(default_factory=dict)
    last_error: str | None = None
    received_at: datetime | None = None
    processing_started_at: datetime | None = None
    processed_at: datetime | None = None
    updated_at: datetime | None = None

