import type { DeliveryStatus } from "@/lib/delivery-status"
const DEFAULT_API_BASE_URL = "/backend"
export interface ApiError extends Error { status?: number }
export interface DriverSummary { driver_id: number; driver_name: string; vehicle_type: string; driver_status: string }
export interface DriverAuthSession { email: string; user_type: string; expires_at: string | null; driver_id: number; driver_name: string; vehicle_type: string; driver_status: string; active_route_group_id?: string | null; active_route_group_name?: string | null; active_zone_code?: string | null }
export interface AvailableShift { route_group_id: string; shift_name: string; zone_code: string; route_group_status: string; total_stops: number; estimated_distance_km: number | null; estimated_duration_min: number | null; scheduled_date: string; first_eta: string | null; last_eta: string | null; warehouse_name: string; warehouse_address: string; stop_preview: string[] }
export interface StartShiftResponse { route_group_id: string; shift_name: string; route_group_status: string; driver_id: number; driver_name: string; vehicle_type: string; driver_status: string; updated_delivery_count: number; external_sync_status: string }
export interface DriverScheduleStop { route_stop_id: string; route_group_id: string; delivery_request_id: string; order_id: number; sequence: number; stop_status: string; estimated_arrival: string | null; address: string | null }
export interface DriverSchedule { driver_id: number; driver_name: string; vehicle_type: string; driver_status: string; stops: DriverScheduleStop[] }
export interface RouteMapCoordinate { latitude: number; longitude: number }
export interface RouteMapWaypoint { latitude: number; longitude: number; label: string; address: string | null; sequence: number | null; route_stop_id: string | null; delivery_request_id: string | null; order_id: number | null; stop_status: string | null }
export interface RouteMapData { route_group_id: string; route_group_name: string; route_group_status: string; routing_status: string; provider: string; warehouse: RouteMapWaypoint; stops: RouteMapWaypoint[]; path: RouteMapCoordinate[]; encoded_polyline: string | null; estimated_distance_km: number | null; estimated_duration_min: number | null; active_origin: RouteMapWaypoint | null; active_stop: RouteMapWaypoint | null; segment_distance_km: number | null; segment_duration_min: number | null; next_stop_eta: string | null }
export interface DeliveryItem { external_item_id: number; item_name: string; quantity: number }
export interface DeliveryCustomerDetails { customer_name: string; phone_number: string; street: string; city: string; province: string; postal_code: string; country: string; latitude: number | null; longitude: number | null; geocode_status: string | null }
export interface DeliveryRecord { id: string; order_id: number; customer_id: number; request_timestamp: string; request_status: string; created_at: string | null; updated_at: string | null; items: DeliveryItem[]; customer_details?: DeliveryCustomerDetails | null }
export interface DeliveryStatusHistoryEntry { status: DeliveryStatus; changed_at: string; changed_by?: string | null; reason?: string | null }
export interface DeliveryTracking { order_id: number; customer_id: number | null; delivery_request_id: string | null; delivery_execution_id: string; delivery_status: DeliveryStatus; latest_status_at: string | null; latest_status_reason: string | null; route_group_id: string | null; route_group_status: string | null; route_stop_id: string | null; stop_sequence: number | null; stop_status: string | null; estimated_arrival: string | null; assigned_driver_id: number | null; assignment_status: string | null; dispatched_at: string | null; out_for_delivery_at: string | null; completed_at: string | null; failed_at: string | null; status_history: DeliveryStatusHistoryEntry[] }

function getApiBaseUrl(): string {
  const configuredBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim()
  return (configuredBaseUrl || DEFAULT_API_BASE_URL).replace(/\/$/, "")
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> { const response = await fetch(`${getApiBaseUrl()}${path}`, { ...init, headers: { "Content-Type": "application/json", ...(init?.headers || {}) }, cache: "no-store" }); if (!response.ok) { let message = `Request failed with HTTP ${response.status}`; try { const payload = await response.json(); if (typeof payload?.detail === "string") message = payload.detail } catch {} const error = new Error(message) as ApiError; error.status = response.status; throw error } return response.json() as Promise<T> }
export const resolveDriverSession = (token: string) => apiFetch<DriverAuthSession>("/api/driver-auth/session", { method: "POST", body: JSON.stringify({ token }) })
export const listAvailableShifts = () => apiFetch<AvailableShift[]>("/api/shifts/available")
export const startShift = (routeGroupId: string, driverId: number) => apiFetch<StartShiftResponse>(`/api/shifts/${routeGroupId}/start`, { method: "POST", body: JSON.stringify({ driver_id: driverId }) })
export const seedDemoData = () => apiFetch<{ driver_accounts: number; available_shifts: number; demo_driver_email: string }>("/api/dev/seed-demo", { method: "POST" })
export const listDrivers = () => apiFetch<DriverSummary[]>("/api/drivers/")
export const getDriverSchedule = (driverId: number, routeGroupId?: string | null) => apiFetch<DriverSchedule>(`/api/driver/schedule/today/${driverId}${routeGroupId ? `?route_group_id=${encodeURIComponent(routeGroupId)}` : ""}`)
export const getRouteMap = (routeGroupId: string) => apiFetch<RouteMapData>(`/api/planning/route-group/${routeGroupId}/map`)
export const getDeliveryRecord = (deliveryRequestId: string) => apiFetch<DeliveryRecord>(`/api/deliveries/${deliveryRequestId}`)
export const getTracking = (orderId: number) => apiFetch<DeliveryTracking>(`/api/delivery-status/${orderId}`)
export const startDelivery = (deliveryExecutionId: string) => apiFetch<{ status: DeliveryStatus; id: string }>(`/api/deliveries/${deliveryExecutionId}/start`, { method: "POST" })
export const completeDelivery = (deliveryExecutionId: string, payload: { received_by: string; proof_of_delivery_url?: string | null }) => apiFetch<{ confirmed: boolean; received_by: string }>(`/api/deliveries/${deliveryExecutionId}/complete`, { method: "POST", body: JSON.stringify(payload) })
export const failDelivery = (deliveryExecutionId: string, payload: { exception_type: string; description: string; retry_allowed: boolean }) => apiFetch<{ exception_type: string; retry_allowed: boolean }>(`/api/deliveries/${deliveryExecutionId}/fail`, { method: "POST", body: JSON.stringify(payload) })
export const completeRouteStop = (routeStopId: string) => apiFetch<{ route_stop_id: string; stop_status: string; message: string }>(`/api/driver/stops/${routeStopId}/complete`, { method: "POST" })
