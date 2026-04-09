"use client"

import { useCallback, useEffect, useState } from "react"

import {
  getDeliveryRecord,
  getDriverSchedule,
  getTracking,
  type DeliveryRecord,
  type DeliveryTracking,
  type DriverSchedule,
  type DriverSummary,
} from "@/lib/api-client"
import type { DeliveryStatus } from "@/lib/delivery-status"

export interface PortalStop {
  routeStopId: string
  routeGroupId: string
  deliveryRequestId: string
  orderId: number
  sequence: number
  stopStatus: string
  estimatedArrival: string | null
  address: string
  customerName: string
  phoneNumber: string | null
  deliveryType: string
  itemSummary: string
  requestStatus: string | null
  deliveryStatus: DeliveryStatus
  deliveryExecutionId: string | null
  assignmentStatus: string | null
  routeGroupStatus: string | null
  tracking: DeliveryTracking | null
  deliveryRecord: DeliveryRecord | null
}

export interface PortalData {
  driver: DriverSummary
  schedule: DriverSchedule
  stops: PortalStop[]
}

function deriveDeliveryStatus(stopStatus: string, tracking: DeliveryTracking | null): DeliveryStatus {
  if (tracking?.delivery_status) {
    return tracking.delivery_status
  }

  if (stopStatus === "completed") {
    return "delivered"
  }

  return "scheduled"
}

function deriveDeliveryType(deliveryRecord: DeliveryRecord | null): string {
  const itemCount = deliveryRecord?.items?.length ?? 0
  return itemCount > 0 ? `${itemCount} item${itemCount === 1 ? "" : "s"}` : "Delivery"
}

function deriveItemSummary(deliveryRecord: DeliveryRecord | null): string {
  if (!deliveryRecord || deliveryRecord.items.length === 0) {
    return "No item details available yet"
  }

  const itemNames = deliveryRecord.items.slice(0, 2).map((item) => `${item.item_name} (${item.quantity})`)
  const remainingCount = deliveryRecord.items.length - itemNames.length
  return remainingCount > 0 ? `${itemNames.join(", ")} +${remainingCount} more` : itemNames.join(", ")
}

async function loadStopDetails(schedule: DriverSchedule): Promise<PortalStop[]> {
  const stops = await Promise.all(
    schedule.stops.map(async (stop) => {
      const [deliveryRecord, tracking] = await Promise.all([
        getDeliveryRecord(stop.delivery_request_id).catch(() => null),
        getTracking(stop.order_id).catch(() => null),
      ])

      const customerDetails = deliveryRecord?.customer_details
      const address = customerDetails
        ? [
            customerDetails.street,
            customerDetails.city,
            customerDetails.province,
            customerDetails.postal_code,
            customerDetails.country,
          ]
            .filter(Boolean)
            .join(", ")
        : stop.address || `Order #${stop.order_id}`

      return {
        routeStopId: stop.route_stop_id,
        routeGroupId: stop.route_group_id,
        deliveryRequestId: stop.delivery_request_id,
        orderId: stop.order_id,
        sequence: stop.sequence,
        stopStatus: stop.stop_status,
        estimatedArrival: stop.estimated_arrival,
        address,
        customerName: customerDetails?.customer_name || `Order #${stop.order_id}`,
        phoneNumber: customerDetails?.phone_number || null,
        deliveryType: deriveDeliveryType(deliveryRecord),
        itemSummary: deriveItemSummary(deliveryRecord),
        requestStatus: deliveryRecord?.request_status ?? null,
        deliveryStatus: deriveDeliveryStatus(stop.stop_status, tracking),
        deliveryExecutionId: tracking?.delivery_execution_id ?? null,
        assignmentStatus: tracking?.assignment_status ?? null,
        routeGroupStatus: tracking?.route_group_status ?? null,
        tracking,
        deliveryRecord,
      } satisfies PortalStop
    }),
  )

  return stops.sort((left, right) => left.sequence - right.sequence)
}

export function useDriverPortalData(driver: DriverSummary | null) {
  const [data, setData] = useState<PortalData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (!driver) {
      setData(null)
      setError(null)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const schedule = await getDriverSchedule(driver.driver_id)
      const stops = await loadStopDetails(schedule)
      setData({ driver, schedule, stops })
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "Unable to load driver route data."
      setError(message)
      setData(null)
    } finally {
      setIsLoading(false)
    }
  }, [driver])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return {
    data,
    isLoading,
    error,
    refresh,
  }
}
