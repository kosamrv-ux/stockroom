# Diagnostic sample: negative inventory adjustments

This is a self-audit of a public build sample, not a claim of client work. It demonstrates the
evidence and handoff included in a small technical diagnosis.

## Reported behavior

The movement model documented `ADJUSTMENT` as bidirectional, but the request schema rejected every
negative quantity. A receipt of 10 followed by a cycle-count adjustment of -4 returned HTTP 422
instead of recording an on-hand balance of 6.

The defect is tracked in
[`stockroom#1`](https://github.com/kosamrv-ux/stockroom/issues/1), including the baseline commit,
minimal reproduction, impact, root cause, fix plan, and acceptance checks.

## Root cause

Two assumptions conflicted:

1. `MovementCreate.quantity` applied a positive-only constraint to every movement kind.
2. `signed_delta` only derived a negative value for shipments and passed every adjustment through
   as a positive increase.

Together they made breakage, shrinkage, and downward stock-take corrections impossible to represent
without misclassifying them as shipments.

## Resolution

- Validate movement quantity according to its kind.
- Keep receipts and shipments as positive magnitudes.
- Accept a signed, non-zero adjustment and preserve its sign in the immutable ledger.
- Apply the existing no-negative-stock check to downward adjustments.
- Cover the valid and invalid direction combinations at the API boundary.

No schema migration is required because the ledger column already stores signed integers.

## Verification

```text
pytest: 20 passed
ruff: All checks passed
alembic check: No new upgrade operations detected
```

The regression test verifies that a receipt of 10 followed by an adjustment of -4 produces an
on-hand balance of 6 and preserves `-4` in movement history. Additional cases reject zero
adjustments, non-positive receipt/shipment magnitudes, and adjustments that would drive stock below
zero.
