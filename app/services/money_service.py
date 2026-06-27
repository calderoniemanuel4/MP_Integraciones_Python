from decimal import ROUND_HALF_UP, Decimal


class MoneyService:
    """Convert money values using minor units. Never use float for persisted amounts."""

    scale_by_currency = {"ARS": 2, "USD": 2, "BRL": 2, "CLP": 0, "COP": 2, "MXN": 2}

    @classmethod
    def to_minor_units(cls, amount: Decimal, currency_id: str) -> int:
        scale = cls.scale_by_currency.get(currency_id.upper(), 2)
        multiplier = Decimal(10) ** scale
        return int((amount * multiplier).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    @classmethod
    def from_minor_units(cls, amount_minor: int, currency_id: str) -> Decimal:
        scale = cls.scale_by_currency.get(currency_id.upper(), 2)
        return (Decimal(amount_minor) / (Decimal(10) ** scale)).quantize(Decimal(10) ** -scale)

    @classmethod
    def decimal_from_mp_amount(cls, amount: str | int | Decimal, currency_id: str) -> int:
        return cls.to_minor_units(Decimal(str(amount)), currency_id)
