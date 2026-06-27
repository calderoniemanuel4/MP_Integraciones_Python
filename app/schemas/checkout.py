from decimal import Decimal

from pydantic import BaseModel, Field


class CheckoutPreferenceRequest(BaseModel):
    product_code: str = Field(default="test-product")
    quantity: int = Field(default=1, gt=0, le=10)


class CheckoutPreferenceResponse(BaseModel):
    order_id: str
    external_reference: str
    preference_id: str
    checkout_url: str
    sandbox_checkout_url: str | None = None


class ProductQuote(BaseModel):
    title: str
    unit_price: Decimal
    currency_id: str = "ARS"

