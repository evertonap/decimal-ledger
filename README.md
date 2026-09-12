# decimal-ledger

A small ledger core built on `Decimal` instead of `float`: balances, transfers, and trade-fill cash effects, with banker's rounding (`ROUND_HALF_EVEN`) applied consistently so repeated postings do not drift.

This is a portfolio/demonstration project. It simulates ledger mechanics only - it does not connect to any real exchange, broker, or payment processor, and should not be used to move real funds as-is.

## Why Decimal, not float

`float` is binary floating point: it cannot represent most decimal fractions exactly, and errors compound across thousands of postings. A ledger that silently drifts by fractions of a cent per transaction eventually fails to reconcile. `Ledger` in this project keeps every balance as a quantized `Decimal` and asserts the invariant that the sum of balances always equals the sum of entries.

## Example

```python
from decimal import Decimal
from ledger.core import Ledger, Fill, apply_fill

ledger = Ledger()
ledger.post("cash", Decimal("10000"), reason="initial deposit")

fill = Fill(side="buy", quantity=Decimal("3"), price=Decimal("142.37"), fee_bps=Decimal("7.5"))
apply_fill(ledger, "cash", fill)

print(ledger.balance("cash"), ledger.total())
```

## Layout

- `ledger/core.py` - `Ledger`, `Fill`, `apply_fill`, `quantize`.
- `tests/test_ledger.py` - invariants: no negative balances, transfers conserve totals, repeated small postings don't drift.

## Status

Demo/portfolio project, not a published package.
