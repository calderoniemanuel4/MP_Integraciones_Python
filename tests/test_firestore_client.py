from unittest.mock import patch

import pytest
from pydantic import SecretStr

from app.config import Settings
from app.firestore.client import create_firestore_client


def test_firestore_client_uses_json_credentials_from_environment() -> None:
    settings = Settings(
        google_cloud_project="project-id",
        google_service_account_json=SecretStr(
            '{"type":"service_account","project_id":"project-id"}'
        ),
    )
    credentials = object()

    with (
        patch(
            "app.firestore.client.service_account.Credentials.from_service_account_info",
            return_value=credentials,
        ) as credentials_factory,
        patch("app.firestore.client.AsyncClient") as client_factory,
    ):
        create_firestore_client(settings)

    credentials_factory.assert_called_once_with(
        {"type": "service_account", "project_id": "project-id"}
    )
    client_factory.assert_called_once_with(project="project-id", credentials=credentials)


@pytest.mark.parametrize("secret", ["not-json", "[]"])
def test_firestore_client_rejects_invalid_json_credentials(secret: str) -> None:
    settings = Settings(
        google_cloud_project="project-id",
        google_service_account_json=SecretStr(secret),
    )

    with pytest.raises(ValueError, match="GOOGLE_SERVICE_ACCOUNT_JSON"):
        create_firestore_client(settings)


@pytest.mark.parametrize("secret", [None, SecretStr("")])
def test_firestore_client_keeps_default_credentials_fallback(
    secret: SecretStr | None,
) -> None:
    settings = Settings(
        google_cloud_project="project-id",
        google_service_account_json=secret,
    )

    with patch("app.firestore.client.AsyncClient") as client_factory:
        create_firestore_client(settings)

    client_factory.assert_called_once_with(project="project-id")
