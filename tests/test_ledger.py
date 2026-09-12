"""Tests for the Decimal-based ledger core."""

from decimal import Decimal

import pytest

from ledger.core import Fill, Ledger, LedgerError, apply_fill, quantize


def test_post_and_balance_roundtrip():
    ledger = Ledger()
    ledger.post("cash", Decimal("100.10000000"), reason="deposit")
    assert ledger.balance("cash") == Decimal("100.10000000")


def test_negative_balance_is_rejected():
    ledger = Ledger()
    ledger.post("cash", Decimal("10"))
    with pytest.raises(LedgerError):
        ledger.post("cash", Decimal("-20"))


def test_transfer_conserves_total():
    ledger = Ledger()
    ledger.post("cash", Decimal("50"))
    ledger.transfer("cash", "fees", Decimal("5.5"))
    assert ledger.total() == Decimal("50.00000000")
    assert ledger.balance("fees") == Decimal("5.50000000")


def test_many_small_transfers_do_not_drift():
    ledger = Ledger()
    ledger.post("cash", Decimal("1000"))
    for _ in range(1000):
        ledger.transfer("cash", "fees", Decimal("0.001"))
    assert ledger.total() == Decimal("1000.00000000")


def test_fill_cash_delta_matches_manual_computation():
    fill = Fill(side="buy", quantity=Decimal("2"), price=Decimal("19.99"), fee_bps=Decimal("10"))
    expected_notional = quantize(Decimal("2") * Decimal("19.99"))
    expected_fee = quantize(expected_notional * Decimal("10") / Decimal(10_000))
    assert fill.cash_delta() == quantize(-(expected_notional + expected_fee))


def test_apply_fill_updates_ledger():
    ledger = Ledger()
    ledger.post("cash", Decimal("1000"))
    fill = Fill(side="sell", quantity=Decimal("1"), price=Decimal("100"), fee_bps=Decimal("5"))
    new_balance = apply_fill(ledger, "cash", fill)
    assert new_balance == ledger.balance("cash")
    assert new_balance > Decimal("1000")
