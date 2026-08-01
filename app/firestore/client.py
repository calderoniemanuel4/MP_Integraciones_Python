import json

from google.cloud.firestore_v1.async_client import AsyncClient
from google.oauth2 import service_account

from app.config import Settings


def create_firestore_client(settings: Settings) -> AsyncClient:
    """Create one reusable async Firestore client.

    FastAPI Cloud can inject a service account JSON through a secret environment variable.
    Local development can keep using Application Default Credentials, a credentials file,
    or the Firestore emulator.
    """

    secret = settings.google_service_account_json
    if secret is None or not secret.get_secret_value().strip():
        return AsyncClient(project=settings.google_cloud_project)

    try:
        service_account_info = json.loads(secret.get_secret_value())
    except json.JSONDecodeError as exc:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON must contain valid JSON") from exc

    if not isinstance(service_account_info, dict):
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON must contain a JSON object")

    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    return AsyncClient(project=settings.google_cloud_project, credentials=credentials)
