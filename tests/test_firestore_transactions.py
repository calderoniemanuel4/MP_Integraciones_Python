from app.services.state_machine import can_transition


def test_transition_rules() -> None:
    assert can_transition("preference_created", "approved")
    assert can_transition("pending", "approved")
    assert not can_transition("approved", "pending")


def test_transaction_helper_documents_no_external_effects_rule() -> None:
    from app.firestore.transactions import run_transaction

    assert "External effects" in (run_transaction.__doc__ or "")
