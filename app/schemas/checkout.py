from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class CheckoutPreferenceRequest(BaseModel):
    product_code: str = "1001"
    quantity: Literal[1] = 1


class CheckoutPreferenceResponse(BaseModel):
    order_id: str
    external_reference: str
    preference_id: str
    checkout_url: str
    sandbox_checkout_url: str | None = None


class ProductQuote(BaseModel):
    product_id: str
    title: str
    description: str
    picture_url: str
    unit_price: Decimal
    currency_id: str = "ARS"
