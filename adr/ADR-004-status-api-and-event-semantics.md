# ADR-004: Persisted status API and explicit event semantics

- Status: Accepted
- Date: 2026-04-08
- Owners: Delivery Execution / Architecture CE
- Related modules: Delivery Execution, Driver Service, Order Orchestration
- Related contracts: `contracts/api-contracts.md`, `contracts/event-contracts.md`

## Context
The original tracking endpoint returned a hardcoded status and did not reflect persisted execution state. The repo also lacked an explicit event-generation boundary even though status transitions already mattered for integration semantics.

## Decision
Use the persisted `DeliveryExecution` aggregate plus `StatusHistory` as the source of truth for the status API. Introduce a lightweight internal event-record table as an outbox-style placeholder so the exact generation point for each event is explicit and testable without adding a real message bus yet.

## Why this shape
- It keeps status vocabulary centralized in the canonical execution state model.
- It gives upstream consumers and the driver UI a useful read model with timeline, route, and assignment context.
- It avoids hidden coupling to a future messaging stack by making event intent visible in persistence first.
- It keeps the event trigger point colocated with the persisted status transition.

## Event semantics
- `DeliveryScheduled`: emitted when scheduling creates the initial execution record.
- `DeliveryDispatched`: emitted when status changes to `out_for_delivery`.
- `DeliveryCompleted`: emitted when status changes to `delivered`.
- `DeliveryFailed`: emitted when status changes to `failed`.

## Consequences
- Orders become trackable only after an execution record exists.
- The status API can now return route/assignment context when planning has already happened.
- Future bus publishing can read from the internal event table rather than searching business tables for changes.
