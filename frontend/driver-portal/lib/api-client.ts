import type { DeliveryStatus } from "@/lib/delivery-status"

const DEFAULT_API_BASE_URL = "http://localhost:8000"

export interface ApiError extends Error {
  status?: number
}

export interface DriverSummary {
  driver_id: number
  driver_name: string
  vehicle_type: string
  driver_status: string
}

export interface DriverScheduleStop {
  route_stop_id: string
  route_group_id: string
  delivery_request_id: string
  order_id: number
  sequence: number
  stop_status: string
  estimated_arrival: string | null
  address: string | null
}

export interface DriverSchedule {
  driver_id: number
  driver_name: string
  vehicle_type: string
  driver_status: string
  stops: DriverScheduleStop[]
}

export interface RouteMapCoordinate {
  latitude: number
  longitude: number
}

export interface RouteMapWaypoint {
  latitude: number
  longitude: number
  label: string
  address: string | null
  sequence: number | null
  route_stop_id: string | null
  delivery_request_id: string | null
  order_id: number | null
  stop_status: string | null
}

export interface RouteMapData {
  route_group_id: string
  route_group_name: string
  route_group_status: string
  routing_status: string
  provider: string
  warehouse: RouteMapWaypoint
  stops: RouteMapWaypoint[]
  path: RouteMapCoordinate[]
  estimated_distance_km: number | null
  estimated_duration_min: number | null
}

export interface DeliveryItem {
  external_item_id: number
  item_name: string
  quantity: number
}

export interface DeliveryCustomerDetails {
  customer_name: string
  phone_number: string
  street: string
  city: string
  province: string
  postal_code: string
  country: string
  latitude: number | null
  longitude: number | null
  geocode_status: string | null
}

export interface DeliveryRecord {
  id: string
  order_id: number
  customer_id: number
  request_timestamp: string
  request_status: string
  created_at: string | null
  updated_at: string | null
  items: DeliveryItem[]
  customer_details?: DeliveryCustomerDetails | null
}

export interface DeliveryStatusHistoryEntry {
  status: DeliveryStatus
  changed_at: string
  changed_by?: string | null
  reason?: string | null
}

export interface DeliveryTracking {
  order_id: number
  customer_id: number | null
  delivery_request_id: string | null
  delivery_execution_id: string
  delivery_status: DeliveryStatus
  latest_status_at: string | null
  latest_status_reason: string | null
  route_group_id: string | null
  route_group_status: string | null
  route_stop_id: string | null
  stop_sequence: number | null
  stop_status: string | null
  estimated_arrival: string | null
  assigned_driver_id: number | null
  assignment_status: string | null
  dispatched_at: string | null
  out_for_delivery_at: string | null
  completed_at: string | null
  failed_at: string | null
  status_history: DeliveryStatusHistoryEntry[]
}

function getApiBaseUrl(): string {
  const configuredBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim()
  return (configuredBaseUrl || DEFAULT_API_BASE_URL).replace(/\/$/, "")
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  })

  if (!response.ok) {
    let message = `Request failed with HTTP ${response.status}`
    try {
      const payload = await response.json()
      if (typeof payload?.detail === "string") {
        message = payload.detail
      }
    } catch {
      // Leave the generic message intact when the backend does not return JSON.
    }

    const error = new Error(message) as ApiError
    error.status = response.status
    throw error
  }

  return response.json() as Promise<T>
}

export function listDrivers(): Promise<DriverSummary[]> {
  return apiFetch<DriverSummary[]>("/api/drivers/")
}

export function getDriverSchedule(driverId: number): Promise<DriverSchedule> {
  return apiFetch<DriverSchedule>(`/api/driver/schedule/today/${driverId}`)
}

export function getRouteMap(routeGroupId: string): Promise<RouteMapData> {
  return apiFetch<RouteMapData>(`/api/planning/route-group/${routeGroupId}/map`)
}

export function getDeliveryRecord(deliveryRequestId: string): Promise<DeliveryRecord> {
  return apiFetch<DeliveryRecord>(`/api/deliveries/${deliveryRequestId}`)
}

export function getTracking(orderId: number): Promise<DeliveryTracking> {
  return apiFetch<DeliveryTracking>(`/api/delivery-status/${orderId}`)
}

export function startDelivery(deliveryExecutionId: string): Promise<{ status: DeliveryStatus; id: string }> {
  return apiFetch<{ status: DeliveryStatus; id: string }>(`/api/deliveries/${deliveryExecutionId}/start`, {
    method: "POST",
  })
}

export function completeDelivery(
  deliveryExecutionId: string,
  payload: { received_by: string; proof_of_delivery_url?: string | null },
): Promise<{ confirmed: boolean; received_by: string }> {
  return apiFetch<{ confirmed: boolean; received_by: string }>(`/api/deliveries/${deliveryExecutionId}/complete`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function failDelivery(
  deliveryExecutionId: string,
  payload: { exception_type: string; description: string; retry_allowed: boolean },
): Promise<{ exception_type: string; retry_allowed: boolean }> {
  return apiFetch<{ exception_type: string; retry_allowed: boolean }>(`/api/deliveries/${deliveryExecutionId}/fail`, {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function completeRouteStop(routeStopId: string): Promise<{ route_stop_id: string; stop_status: string; message: string }> {
  return apiFetch<{ route_stop_id: string; stop_status: string; message: string }>(`/api/driver/stops/${routeStopId}/complete`, {
    method: "POST",
  })
}
