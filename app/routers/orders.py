from fastapi import APIRouter, Depends, HTTPException, Query
from google.cloud.firestore_v1.async_client import AsyncClient

from app.dependencies import firestore_client_dep
from app.models.order import Order
from app.repositories.order_repository import OrderRepository

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    client: AsyncClient = Depends(firestore_client_dep),
) -> Order:
    order = await OrderRepository(client).get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("", response_model=list[Order])
async def list_orders(
    status: str = Query(default="preference_created"),
    limit: int = Query(default=50, ge=1, le=100),
    client: AsyncClient = Depends(firestore_client_dep),
) -> list[Order]:
    return await OrderRepository(client).list_by_status(status, limit)
