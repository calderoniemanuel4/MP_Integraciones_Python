from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

OrderInternalStatus = Literal[
    "created",
    "preference_created",
    "pending",
    "approved",
    "rejected",
    "cancelled",
    "refunded",
    "charged_back",
    "error",
    "manual_review",
]


class Order(BaseModel):
    order_id: str
    external_reference: str
    title: str
    quantity: int = Field(gt=0)
    unit_price_minor: int = Field(ge=0)
    total_amount_minor: int = Field(ge=0)
    currency_id: str
    preference_id: str | None = None
    checkout_url: str | None = None
    sandbox_checkout_url: str | None = None
    internal_status: OrderInternalStatus = "created"
    mp_payment_status: str | None = None
    mp_payment_status_detail: str | None = None
    mercado_pago_payment_id: str | None = None
    live_mode: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_payment_update_at: datetime | None = None

