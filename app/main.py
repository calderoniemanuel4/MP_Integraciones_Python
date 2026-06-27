from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from inspect import isawaitable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.firestore.client import create_firestore_client
from app.logging_config import configure_logging
from app.routers import checkout, health, orders, payments, returns, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    app.state.firestore_client = create_firestore_client(get_settings())
    yield
    close_result = app.state.firestore_client.close()
    if isawaitable(close_result):
        await close_result


app = FastAPI(title="MP Checkout Pro Firestore", version="0.1.0", lifespan=lifespan)
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "x-signature", "x-request-id"],
)

app.include_router(health.router)
app.include_router(checkout.router)
app.include_router(returns.router)
app.include_router(webhooks.router)
app.include_router(orders.router)
app.include_router(payments.router)
