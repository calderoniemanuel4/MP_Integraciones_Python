from app.config import Settings
from app.services.mercado_pago_service import MercadoPagoService


async def test_client_sends_integrator_id_header() -> None:
    service = MercadoPagoService(
        Settings(
            mp_access_token="token",
            mp_integrator_id="dev_24c65fb163bf11ea96500242ac130004",
        )
    )

    try:
        assert (
            service.client.headers["x-integrator-id"]
            == "dev_24c65fb163bf11ea96500242ac130004"
        )
        assert service.client.headers["authorization"] == "Bearer token"
    finally:
        await service.client.aclose()
