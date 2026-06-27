from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Payment(BaseModel):
    mercado_pago_payment_id: str
    order_id: str | None = None
    external_reference: str | None = None
    status: str
    status_detail: str | None = None
    transaction_amount_minor: int | None = Field(default=None, ge=0)
    currency_id: str | None = None
    payment_type_id: str | None = None
    payment_method_id: str | None = None
    installments: int | None = None
    live_mode: bool | None = None
    date_created: datetime | None = None
    date_approved: datetime | None = None
    date_last_updated: datetime | None = None
    raw_payment: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

