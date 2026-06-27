from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    environment: str = "development"
    mp_access_token: str = Field(default="", validation_alias="MP_ACCESS_TOKEN")
    mp_public_key: str = Field(default="", validation_alias="MP_PUBLIC_KEY")
    mp_webhook_secret: str = Field(default="", validation_alias="MP_WEBHOOK_SECRET")
    base_url: AnyHttpUrl | str = Field(default="http://localhost:8000", validation_alias="BASE_URL")
    mp_success_url: AnyHttpUrl | str = Field(
        default="http://localhost:8000/checkout/success", validation_alias="MP_SUCCESS_URL"
    )
    mp_failure_url: AnyHttpUrl | str = Field(
        default="http://localhost:8000/checkout/failure", validation_alias="MP_FAILURE_URL"
    )
    mp_pending_url: AnyHttpUrl | str = Field(
        default="http://localhost:8000/checkout/pending", validation_alias="MP_PENDING_URL"
    )
    mp_webhook_url: AnyHttpUrl | str = Field(
        default="http://localhost:8000/webhooks/mercadopago", validation_alias="MP_WEBHOOK_URL"
    )
    google_cloud_project: str = Field(
        default="mp-checkout-pro-test", validation_alias="GOOGLE_CLOUD_PROJECT"
    )
    local_frontend_origin: str = Field(
        default="http://localhost:5500", validation_alias="LOCAL_FRONTEND_ORIGIN"
    )
    use_firestore_emulator: bool = Field(default=False, validation_alias="USE_FIRESTORE_EMULATOR")
    firestore_emulator_host: str | None = Field(
        default=None, validation_alias="FIRESTORE_EMULATOR_HOST"
    )
    mp_api_base_url: str = "https://api.mercadopago.com"
    request_timeout_seconds: float = 10.0

    @property
    def allowed_origins(self) -> list[str]:
        return [self.local_frontend_origin, "http://127.0.0.1:5500"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
