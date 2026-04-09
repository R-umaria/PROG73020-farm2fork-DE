# ADR-003: Deterministic default driver assignment for scheduled route groups

- Status: Accepted
- Date: 2026-04-08
- Owners: Delivery Execution Team
- Related contracts: `contracts/api-contracts.md`

## Context
The planning flow now needs to turn grouped backlog into concrete `RouteGroup` and `RouteStop` records. Once a route group exists, the service also needs an explicit rule for choosing a driver so assignment behavior is explainable and testable instead of being hidden inside ad hoc repository code.

This step is intentionally limited to a simple scheduling and assignment heuristic. It does not attempt route optimization, ETA optimization, or geographic balancing.

## Decision
Use a two-step deterministic planning rule:

1. **Scheduling rule**
   - create one `RouteGroup` per grouped backlog partition
   - keep stop order deterministic by reusing the grouped candidate order: `request_timestamp`, then `order_id`, then `delivery_request_id`
   - use the earliest candidate timestamp in the group as the route group's `scheduled_date`
   - create simple estimated arrivals in 15-minute increments from that scheduled date

2. **Driver assignment rule**
   - evaluate only drivers whose status is `available`
   - prefer the driver with the lowest current active assignment load
   - break ties by `driver_id`, then driver name

The selection rule is isolated behind `DriverAssignmentPolicy` so later iterations can swap the policy without rewriting the scheduling orchestration.

## Why this stays intentionally simple
- The current project needs an explicit, reviewable default rather than an opaque optimization engine.
- A deterministic heuristic is easier to test, demo, and defend during integration.
- Separating policy from orchestration keeps later enhancements local to one rule layer.

## Alternatives considered
1. Round-robin assignment without checking current load.
2. Complex geographic or time-window optimization.
3. Assign no drivers until a later planning phase.

## Trade-offs
### Pros
- Repeatable route and assignment output for the same input state.
- Clear explanation for why a particular driver was selected.
- Easy to replace the rule later without changing route persistence code.

### Cons
- Current load is a coarse proxy for capacity.
- Does not consider driver vehicle constraints, hours, or geography yet.
- Estimated arrivals are placeholders for sequencing only, not real ETA predictions.

## Consequences
- The repo now persists route groups, route stops, and driver assignments through a single planning path.
- Assignment behavior is explicit in code and documentation rather than implied.
- Future optimization work should update this ADR instead of quietly changing the selection rule.
