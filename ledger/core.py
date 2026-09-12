"""
ledger.core
===========

A small, dependency-free ledger core built around `decimal.Decimal` instead
of `float`, for the class of systems where correctness of money arithmetic
matters more than raw speed: balances, fills, fees, and P&L.

This is a demonstration/portfolio project. It simulates ledger mechanics;
it does not connect to any real exchange, broker, or payment processor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Dict, List


class LedgerError(Exception):
    """Raised when an operation would violate ledger invariants."""


def quantize(amount: Decimal, exponent: str = "0.00000001") -> Decimal:
    """Round `amount` to a fixed number of decimal places using banker's
    rounding (ROUND_HALF_EVEN), the same convention most real ledgers use to
    avoid systematic bias when rounding a large number of transactions.
    """
    try:
        return amount.quantize(Decimal(exponent), rounding=ROUND_HALF_EVEN)
    except InvalidOperation as exc:
        raise LedgerError(f"cannot quantize {amount!r}") from exc


@dataclass
class Entry:
    """A single signed movement against an account, for audit purposes."""

    account: str
    amount: Decimal
    reason: str


@dataclass
class Ledger:
    """An in-memory, append-only ledger of Decimal balances.

    Every mutation goes through :meth:`post`, which keeps a full history in
    `entries` and guarantees the ledger never silently drifts: the sum of
    all entries always equals the sum of current balances.
    """

    balances: Dict[str, Decimal] = field(default_factory=dict)
    entries: List[Entry] = field(default_factory=list)

    def balance(self, account: str) -> Decimal:
        return self.balances.get(account, Decimal("0"))

    def post(self, account: str, amount: Decimal, reason: str = "") -> Decimal:
        """Apply a signed `amount` to `account` and record the entry."""
        amount = quantize(Decimal(amount))
        new_balance = quantize(self.balance(account) + amount)
        if new_balance < 0:
            raise LedgerError(
                f"posting {amount} to {account!r} would go negative "
                f"({self.balance(account)} -> {new_balance})"
            )
        self.balances[account] = new_balance
        self.entries.append(Entry(account=account, amount=amount, reason=reason))
        return new_balance

    def transfer(self, src: str, dst: str, amount: Decimal, reason: str = "") -> None:
        """Move `amount` from `src` to `dst` as a single atomic pair."""
        amount = quantize(Decimal(amount))
        self.post(src, -amount, reason or f"transfer to {dst}")
        self.post(dst, amount, reason or f"transfer from {src}")

    def total(self) -> Decimal:
        """Sum of every balance currently on the ledger."""
        return quantize(sum(self.balances.values(), Decimal("0")))

    def sum_of_entries(self) -> Decimal:
        """Sum of every entry ever posted; should reconcile against `total()`
        for accounts that started at zero.
        """
        return quantize(sum((e.amount for e in self.entries), Decimal("0")))


@dataclass(frozen=True)
class Fill:
    """A single simulated trade fill."""

    side: str  # "buy" or "sell"
    quantity: Decimal
    price: Decimal
    fee_bps: Decimal = Decimal("0")

    def notional(self) -> Decimal:
        return quantize(self.quantity * self.price)

    def fee(self) -> Decimal:
        return quantize(self.notional() * self.fee_bps / Decimal(10_000))

    def cash_delta(self) -> Decimal:
        """Signed cash impact of this fill, fee included."""
        gross = self.notional()
        fee = self.fee()
        if self.side == "buy":
            return quantize(-(gross + fee))
        if self.side == "sell":
            return quantize(gross - fee)
        raise LedgerError(f"unknown side {self.side!r}")


def apply_fill(ledger: Ledger, account: str, fill: Fill) -> Decimal:
    """Post the cash effect of `fill` to `account` and return the new balance."""
    return ledger.post(account, fill.cash_delta(), reason=f"fill:{fill.side}:{fill.quantity}@{fill.price}")
