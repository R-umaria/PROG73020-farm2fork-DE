# ADR-002: Deterministic backlog grouping by region for planning

- Status: Accepted
- Date: 2026-04-08
- Owners: Delivery Execution Team
- Related contracts: `contracts/api-contracts.md`

## Context
The repo's planning flow exposed a `group_backlog` placeholder with no actual domain behavior. Route planning needs a stable pre-scheduling grouping rule so later scheduling and assignment steps consume the same backlog partitioning logic instead of recreating ad hoc region heuristics in different layers.

This step is intentionally limited to grouping. It does not schedule routes, choose drivers, or introduce route optimization.

## Decision
Implement backlog grouping as deterministic domain logic in `PlanningService.group_backlog()`.

Eligibility for grouping:
- the delivery request is not already attached to a `RouteStop`
- customer enrichment exists
- customer enrichment contains non-empty `street`, `city`, `province`, and `country`

Region derivation:
1. Use the normalized postal prefix first when a usable postal code exists.
2. Fall back to normalized `city + province` when postal prefix is unavailable.

Handling split:
- grouping keys include handling type so `pickup` and `delivery` requests remain separate when the intake snapshot carries `order_type`
- when `order_type` is absent, the current implementation defaults to `delivery`

Determinism:
- group keys are explicit strings derived from normalized inputs
- groups are returned in lexicographic key order
- members within each group are sorted by `request_timestamp`, then `order_id`, then `delivery_request_id`

## Why this avoids hidden coupling
The grouping rule depends only on data owned by Delivery Execution:
- the persisted delivery request
- the customer enrichment snapshot already stored in this service
- the explicit intake snapshot field `order_type` when present

It does not depend on UI labels, driver availability, routing vendors, or another module's private persistence model. That keeps the grouping rule stable and testable while later scheduling logic can build on the same output without duplicating inference rules.

## Alternatives considered
1. Group only by city and province.
2. Group directly by latitude/longitude or external geohash.
3. Defer grouping until route scheduling and compute regions inline there.

## Trade-offs
### Pros
- Predictable and repeatable grouping output across runs.
- Clear fallback behavior when postal codes are missing or inconsistent.
- Keeps planning logic in one service-owned place instead of scattering it across routes or UI code.

### Cons
- Postal-prefix grouping is coarse and not an optimization strategy.
- The current fallback may still over-group dense cities until later scheduling refinement exists.
- `order_type` handling is limited to what is present in the stored intake snapshot.

## Consequences
- Planning can now expose a reusable backlog partitioning output for later route scheduling work.
- Requests missing required enrichment remain visible through explicit skip reasons instead of silently disappearing.
- Future changes to grouping rules should update this ADR and the planning contract together.
