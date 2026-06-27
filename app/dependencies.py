from collections.abc import AsyncIterator

from fastapi import Depends, Request
from google.cloud.firestore_v1.async_client import AsyncClient

from app.config import Settings, get_settings
from app.repositories.alert_repository import PaymentAlertRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.webhook_repository import WebhookEventRepository
from app.services.mercado_pago_service import MercadoPagoService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.webhook_service import WebhookService


def settings_dep() -> Settings:
    return get_settings()


def firestore_client_dep(request: Request) -> AsyncClient:
    return request.app.state.firestore_client


async def mercado_pago_service_dep(request: Request) -> AsyncIterator[MercadoPagoService]:
    service = MercadoPagoService(get_settings())
    try:
        yield service
    finally:
        await service.client.aclose()


def order_repository_dep(client: AsyncClient = Depends(firestore_client_dep)) -> OrderRepository:
    return OrderRepository(client)


def payment_repository_dep(
    client: AsyncClient = Depends(firestore_client_dep),
) -> PaymentRepository:
    return PaymentRepository(client)


def alert_repository_dep(
    client: AsyncClient = Depends(firestore_client_dep),
) -> PaymentAlertRepository:
    return PaymentAlertRepository(client)


def webhook_repository_dep(
    client: AsyncClient = Depends(firestore_client_dep),
) -> WebhookEventRepository:
    return WebhookEventRepository(client)


def order_service_dep(
    order_repository: OrderRepository = Depends(order_repository_dep),
    mercado_pago_service: MercadoPagoService = Depends(mercado_pago_service_dep),
    settings: Settings = Depends(settings_dep),
) -> OrderService:
    return OrderService(order_repository, mercado_pago_service, settings)


def payment_service_dep(
    order_repository: OrderRepository = Depends(order_repository_dep),
    payment_repository: PaymentRepository = Depends(payment_repository_dep),
    alert_repository: PaymentAlertRepository = Depends(alert_repository_dep),
) -> PaymentService:
    return PaymentService(order_repository, payment_repository, alert_repository)


def webhook_service_dep(
    webhook_repository: WebhookEventRepository = Depends(webhook_repository_dep),
    mercado_pago_service: MercadoPagoService = Depends(mercado_pago_service_dep),
    payment_service: PaymentService = Depends(payment_service_dep),
) -> WebhookService:
    return WebhookService(
        get_settings(),
        webhook_repository,
        mercado_pago_service,
        payment_service,
    )
