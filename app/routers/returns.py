import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import mercado_pago_service_dep, payment_service_dep
from app.services.mercado_pago_service import MercadoPagoAPIError, MercadoPagoService
from app.services.money_service import MoneyService
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/checkout", tags=["returns"])
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


def normalize_mp_query_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized or normalized.lower() in {"null", "none"}:
        return None
    return normalized


async def render_result(
    request: Request,
    outcome: str,
    payment_id: str | None,
    mp: MercadoPagoService,
    payment_service: PaymentService,
    status: str | None = None,
    external_reference: str | None = None,
    preference_id: str | None = None,
) -> HTMLResponse:
    if payment_id is None:
        if external_reference:
            try:
                await payment_service.mark_checkout_cancelled(external_reference)
            except Exception:
                # A back URL must still render if Firestore is temporarily unavailable.
                logger.exception(
                    "Could not mark checkout cancelled external_reference=%s",
                    external_reference,
                )
        return templates.TemplateResponse(
            request,
            "payment_result.html",
            context={
                "request": request,
                "outcome": outcome,
                "payment": None,
                "verified": False,
                "display_amount": "-",
                "return_status": status,
                "external_reference": external_reference,
                "preference_id": preference_id,
            },
        )
    try:
        raw_payment = await mp.get_payment(payment_id)
        payment = await payment_service.reconcile_payment(raw_payment)
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
    display_amount = "-"
    if payment.transaction_amount_minor is not None and payment.currency_id:
        amount = MoneyService.from_minor_units(
            payment.transaction_amount_minor,
            payment.currency_id,
        )
        display_amount = f"{payment.currency_id} {amount}"
    return templates.TemplateResponse(
        request,
        "payment_result.html",
        context={
            "request": request,
            "outcome": outcome,
            "payment": payment,
            "verified": True,
            "display_amount": display_amount,
            "return_status": status,
            "external_reference": external_reference,
            "preference_id": preference_id,
        },
    )


@router.get("/success", response_class=HTMLResponse)
async def success(
    request: Request,
    payment_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    external_reference: str | None = Query(default=None),
    preference_id: str | None = Query(default=None),
    mp: MercadoPagoService = Depends(mercado_pago_service_dep),
    payment_service: PaymentService = Depends(payment_service_dep),
) -> HTMLResponse:
    return await render_result(
        request,
        "success",
        normalize_mp_query_value(payment_id),
        mp,
        payment_service,
        normalize_mp_query_value(status),
        normalize_mp_query_value(external_reference),
        normalize_mp_query_value(preference_id),
    )


@router.get("/failure", response_class=HTMLResponse)
async def failure(
    request: Request,
    payment_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    external_reference: str | None = Query(default=None),
    preference_id: str | None = Query(default=None),
    mp: MercadoPagoService = Depends(mercado_pago_service_dep),
    payment_service: PaymentService = Depends(payment_service_dep),
) -> HTMLResponse:
    return await render_result(
        request,
        "failure",
        normalize_mp_query_value(payment_id),
        mp,
        payment_service,
        normalize_mp_query_value(status),
        normalize_mp_query_value(external_reference),
        normalize_mp_query_value(preference_id),
    )


@router.get("/pending", response_class=HTMLResponse)
async def pending(
    request: Request,
    payment_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    external_reference: str | None = Query(default=None),
    preference_id: str | None = Query(default=None),
    mp: MercadoPagoService = Depends(mercado_pago_service_dep),
    payment_service: PaymentService = Depends(payment_service_dep),
) -> HTMLResponse:
    return await render_result(
        request,
        "pending",
        normalize_mp_query_value(payment_id),
        mp,
        payment_service,
        normalize_mp_query_value(status),
        normalize_mp_query_value(external_reference),
        normalize_mp_query_value(preference_id),
    )
