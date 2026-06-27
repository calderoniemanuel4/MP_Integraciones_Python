from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import order_service_dep
from app.schemas.checkout import CheckoutPreferenceRequest, CheckoutPreferenceResponse
from app.services.mercado_pago_service import MercadoPagoAPIError
from app.services.order_service import OrderService

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("/preference", response_model=CheckoutPreferenceResponse)
async def create_preference(
    payload: CheckoutPreferenceRequest,
    service: OrderService = Depends(order_service_dep),
) -> CheckoutPreferenceResponse:
    try:
        return await service.create_checkout_preference(payload)
    except MercadoPagoAPIError as exc:
        raise HTTPException(status_code=502, detail="Mercado Pago preference error") from exc
