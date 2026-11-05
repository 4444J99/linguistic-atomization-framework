# ARC4N Protocol Tracker

Objective: enforce a strict `proposed -> approved -> built -> receipted` lifecycle so no artifact remains in limbo.

## Protocol States

| State | Meaning | Required Output |
|---|---|---|
| `PROPOSED` | Idea has been suggested, not approved | Proposal row in tracker |
| `APPROVED` | User approved build | Build ticket ID + owner |
| `BUILT` | Artifact created | Absolute file path + checksum |
| `RECEIPTED` | Build acknowledged and logged | Save receipt entry |

## Mandatory Gates

1. Confirm-Build-Close: every proposed artifact must be explicitly accepted/rejected.
2. Artifact Receipts: every built artifact must produce a save receipt.
3. Thread Forking: creative build threads and management threads remain separate.
4. Weekly Reconciliation: compare proposal list to built artifacts and close gaps.

## Current Protocol Baseline

- Confirm-Build-Close: active in this repository tracker set.
- Artifact Receipts: active (`Save_Receipt_2026-02-18.md`).
- Thread Forking model: represented by separate plan buckets (`AB-PLAN-*`).
- Reconciliation cadence: pending automation (`AB-PLAN-04`).
