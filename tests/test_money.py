from decimal import Decimal

from app.services.money_service import MoneyService


def test_decimal_to_minor_units() -> None:
    assert MoneyService.to_minor_units(Decimal("1500.00"), "ARS") == 150000
    assert MoneyService.from_minor_units(150000, "ARS") == Decimal("1500.00")

