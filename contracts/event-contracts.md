# Event Contracts

Track important state changes here.

## Canonical delivery execution status vocabulary
- `scheduled`
- `out_for_delivery`
- `delivered`
- `failed`

## Current event/state flow
1. `DeliveryScheduled` → execution enters `scheduled`
2. `DeliveryOutForDelivery` → execution transitions to `out_for_delivery`
3. `DeliveryDelivered` → execution transitions to `delivered`
4. `DeliveryFailed` → execution transitions to `failed`

## Allowed transitions
- `scheduled` → `out_for_delivery`
- `scheduled` → `failed`
- `out_for_delivery` → `delivered`
- `out_for_delivery` → `failed`
- `delivered` and `failed` are terminal for the current implementation
