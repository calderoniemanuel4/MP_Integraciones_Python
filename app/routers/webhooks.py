from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.dependencies import webhook_repository_dep, webhook_service_dep
from app.repositories.webhook_repository import WebhookEventRepository
from app.services.webhook_service import InvalidWebhookSignature, WebhookService

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/mercadopago")
async def mercado_pago_webhook(
    request: Request,
    x_signature: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    service: WebhookService = Depends(webhook_service_dep),
) -> dict[str, str]:
    payload = await request.json()
    try:
        event_key = await service.process_webhook(
            payload=payload,
            x_signature=x_signature,
            x_request_id=x_request_id,
            query_data_id=request.query_params.get("data.id"),
        )
    except InvalidWebhookSignature as exc:
        raise HTTPException(status_code=401, detail="Invalid Mercado Pago signature") from exc
    return {"status": "ok", "event_key": event_key}


@router.get("/webhooks/{event_key}")
async def get_webhook_event(
    event_key: str,
    webhook_repository: WebhookEventRepository = Depends(webhook_repository_dep),
) -> dict:
    event = await webhook_repository.get(event_key)
    if event is None:
        raise HTTPException(status_code=404, detail="Webhook event not found")
    return event.model_dump(mode="json")
