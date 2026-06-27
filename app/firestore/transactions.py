from collections.abc import Awaitable, Callable
from typing import TypeVar

from google.cloud.firestore_v1.async_client import AsyncClient

T = TypeVar("T")


async def run_transaction(client: AsyncClient, callback: Callable[[object], Awaitable[T]]) -> T:
    """Run an async Firestore transaction.

    External effects such as HTTP calls must happen before this helper is invoked because
    Firestore transactions can be retried.
    """

    transaction = client.transaction()
    return await callback(transaction)

