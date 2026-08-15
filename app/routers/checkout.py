from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.dependencies import order_service_dep
from app.schemas.checkout import (
    CheckoutConfigResponse,
    CheckoutPreferenceRequest,
    CheckoutPreferenceResponse,
)
from app.services.mercado_pago_service import MercadoPagoAPIError
from app.services.order_service import OrderService

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.get("/config", response_model=CheckoutConfigResponse)
async def checkout_config(settings: Settings = Depends(get_settings)) -> CheckoutConfigResponse:
    public_key = settings.mp_public_key.strip()
    if not public_key:
        raise HTTPException(status_code=503, detail="Mercado Pago Public Key is not configured")
    return CheckoutConfigResponse(public_key=public_key)


@router.post("/preference", response_model=CheckoutPreferenceResponse)
async def create_preference(
    payload: CheckoutPreferenceRequest,
    service: OrderService = Depends(order_service_dep),
) -> CheckoutPreferenceResponse:
    try:
        return await service.create_checkout_preference(payload)
    except MercadoPagoAPIError as exc:
        raise HTTPException(status_code=502, detail="Mercado Pago preference error") from exc
