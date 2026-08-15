from decimal import Decimal

from pydantic import BaseModel, Field


class CheckoutPreferenceRequest(BaseModel):
    product_code: str = "1001"
    quantity: int = Field(default=1, ge=1, le=3)


class CheckoutPreferenceResponse(BaseModel):
    order_id: str
    external_reference: str
    preference_id: str
    checkout_url: str
    sandbox_checkout_url: str | None = None


class CheckoutConfigResponse(BaseModel):
    public_key: str


class ProductQuote(BaseModel):
    product_id: str
    title: str
    description: str
    picture_url: str
    unit_price: Decimal
    currency_id: str = "ARS"
