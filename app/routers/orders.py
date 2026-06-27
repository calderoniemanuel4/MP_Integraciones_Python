from fastapi import APIRouter, Depends, HTTPException, Query
from google.cloud.firestore_v1.async_client import AsyncClient

from app.dependencies import firestore_client_dep
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    client: AsyncClient = Depends(firestore_client_dep),
) -> OrderResponse:
    order = await OrderRepository(client).get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse(**order.model_dump())


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    status: str = Query(default="preference_created"),
    limit: int = Query(default=50, ge=1, le=100),
    client: AsyncClient = Depends(firestore_client_dep),
) -> list[OrderResponse]:
    orders = await OrderRepository(client).list_by_status(status, limit)
    return [OrderResponse(**order.model_dump()) for order in orders]
