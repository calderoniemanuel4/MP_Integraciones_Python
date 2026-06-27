from google.cloud.firestore_v1.async_client import AsyncClient

from app.config import Settings


def create_firestore_client(settings: Settings) -> AsyncClient:
    """Create one reusable async Firestore client.

    Authentication is handled by Application Default Credentials locally, IAM on Google Cloud,
    or the FIRESTORE_EMULATOR_HOST environment variable for the emulator.
    """

    return AsyncClient(project=settings.google_cloud_project)

