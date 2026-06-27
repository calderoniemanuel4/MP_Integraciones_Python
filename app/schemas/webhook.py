from typing import Any

from pydantic import BaseModel, Field


class WebhookPayload(BaseModel):
    id: str | None = None
    type: str | None = None
    action: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    live_mode: bool | None = None

