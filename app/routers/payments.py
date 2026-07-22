from fastapi import APIRouter, Depends, HTTPException
from google.cloud.firestore_v1.async_client import AsyncClient

from app.dependencies import firestore_client_dep
from app.models.payment import Payment
from app.repositories.alert_repository import PaymentAlertRepository
from app.repositories.payment_repository import PaymentRepository

router = APIRouter(tags=["payments"])


@router.get("/payments/{payment_id}", response_model=Payment)
async def get_payment(
    payment_id: str,
    client: AsyncClient = Depends(firestore_client_dep),
) -> Payment:
    payment = await PaymentRepository(client).get(payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.get("/alerts")
async def list_alerts(
    limit: int = 50,
    client: AsyncClient = Depends(firestore_client_dep),
) -> list[dict]:
    alerts = await PaymentAlertRepository(client).list_unresolved(limit)
    return [alert.model_dump(mode="json") for alert in alerts]
