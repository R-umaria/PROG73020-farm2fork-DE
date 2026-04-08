# ADR-001: Canonical delivery execution status state model

- Status: Accepted
- Date: 2026-04-08
- Owners: Delivery Execution Team
- Related contracts: `contracts/api-contracts.md`, `contracts/event-contracts.md`

## Context
The repo used multiple free-form delivery status strings such as `scheduled`, `Out for Delivery`, and `Delivered`. That created avoidable drift between backend code, HTTP responses, event documentation, and the React driver portal.

The current implementation scope is delivery execution only. Planning, intake persistence, retry orchestration, message bus behavior, and richer stop or assignment state models are intentionally out of scope for this change.

## Decision
Adopt one canonical delivery execution status vocabulary for the current repo:
- `scheduled`
- `out_for_delivery`
- `delivered`
- `failed`

Allowed transitions for the current implementation:
- `scheduled` → `out_for_delivery`
- `scheduled` → `failed`
- `out_for_delivery` → `delivered`
- `out_for_delivery` → `failed`

`delivered` and `failed` are terminal states in the current implementation.

The execution repository is the enforcement point for transition validation. Delivery action endpoints surface invalid transitions as `409 Conflict` instead of silently accepting inconsistent state changes.

## Alternatives considered
1. Keep free-form strings and rely on conventions.
2. Add a larger workflow engine or generalized state machine framework.
3. Introduce execution, stop, assignment, and route state models all at once.

## Trade-offs
### Pros
- One vocabulary across backend code, contracts, and frontend display logic.
- Invalid transitions fail early in a predictable place.
- Small change footprint with a clear extension point for later states.

### Cons
- The current implementation keeps a deliberately narrow status set.
- Future workflow steps such as dispatch or retry will require an ADR update and transition expansion.

## Consequences
- Existing code paths that wrote mixed-case or spaced status strings now normalize to canonical values.
- Delivery action callers must respect transition order.
- Tests now cover valid and invalid transitions directly.
