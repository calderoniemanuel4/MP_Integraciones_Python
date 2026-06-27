from datetime import datetime
from typing import Literal

from pydantic import BaseModel

AlertType = Literal[
    "amount_mismatch",
    "currency_mismatch",
    "order_not_found",
    "invalid_state_transition",
    "payment_without_external_reference",
    "payment_api_error",
    "webhook_processing_error",
]


class PaymentAlert(BaseModel):
    alert_id: str
    type: AlertType
    severity: str
    order_id: str | None = None
    payment_id: str | None = None
    expected_value: str | None = None
    received_value: str | None = None
    message: str
    resolved: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

