from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from google.cloud.firestore_v1.async_client import AsyncClient

from app.dependencies import firestore_client_dep, mercado_pago_service_dep
from app.repositories.alert_repository import PaymentAlertRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.payment_repository import PaymentRepository
from app.services.mercado_pago_service import MercadoPagoAPIError, MercadoPagoService
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/checkout", tags=["returns"])
templates = Jinja2Templates(directory="app/templates")


async def render_result(
    request: Request,
    outcome: str,
    payment_id: str | None,
    client: AsyncClient,
    mp: MercadoPagoService,
) -> HTMLResponse:
    if not payment_id:
        return templates.TemplateResponse(
            request,
            "error.html",
            context={
                "request": request,
                "message": "No se recibió payment_id. No se puede verificar el pago.",
            },
            status_code=400,
        )
    try:
        raw_payment = await mp.get_payment(payment_id)
        payment = await PaymentService(
            OrderRepository(client), PaymentRepository(client), PaymentAlertRepository(client)
        ).reconcile_payment(raw_payment)
    except MercadoPagoAPIError:
        return templates.TemplateResponse(
            request,
            "error.html",
            context={
                "request": request,
                "message": "No se pudo verificar el pago contra Mercado Pago.",
            },
            status_code=502,
        )
    return templates.TemplateResponse(
        request,
        "payment_result.html",
        context={
            "request": request,
            "outcome": outcome,
            "payment": payment,
            "verified": True,
        },
    )


@router.get("/success", response_class=HTMLResponse)
async def success(
    request: Request,
    payment_id: str | None = Query(default=None),
    client: AsyncClient = Depends(firestore_client_dep),
    mp: MercadoPagoService = Depends(mercado_pago_service_dep),
) -> HTMLResponse:
    return await render_result(request, "success", payment_id, client, mp)


@router.get("/failure", response_class=HTMLResponse)
async def failure(
    request: Request,
    payment_id: str | None = Query(default=None),
    client: AsyncClient = Depends(firestore_client_dep),
    mp: MercadoPagoService = Depends(mercado_pago_service_dep),
) -> HTMLResponse:
    return await render_result(request, "failure", payment_id, client, mp)


@router.get("/pending", response_class=HTMLResponse)
async def pending(
    request: Request,
    payment_id: str | None = Query(default=None),
    client: AsyncClient = Depends(firestore_client_dep),
    mp: MercadoPagoService = Depends(mercado_pago_service_dep),
) -> HTMLResponse:
    return await render_result(request, "pending", payment_id, client, mp)
