from app.models.order import Order


def test_order_doc_id_matches_order_id() -> None:
    order = Order(
        order_id="order-1",
        external_reference="order-1",
        title="Producto",
        quantity=1,
        unit_price_minor=150000,
        total_amount_minor=150000,
        currency_id="ARS",
    )
    assert order.order_id == order.external_reference

