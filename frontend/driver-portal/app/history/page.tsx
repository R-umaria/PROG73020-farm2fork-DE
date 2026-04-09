"use client"

import { useMemo } from "react"
import { AlertTriangle, History, PackageCheck } from "lucide-react"

import { AppShell } from "@/components/delivery/app-shell"
import { DeliveryCard } from "@/components/delivery/delivery-card"
import { PageHeader } from "@/components/delivery/page-header"
import { StatePanel } from "@/components/delivery/state-panel"
import { Spinner } from "@/components/ui/spinner"
import { useDriverPortalData } from "@/hooks/use-driver-portal-data"
import { useDriverSession } from "@/hooks/use-driver-session"
import { formatTimeWindow } from "@/lib/portal-formatters"

export default function HistoryPage() {
  const { session, isReady } = useDriverSession({ required: true })
  const driver = session
    ? {
        driver_id: session.driverId,
        driver_name: session.driverName,
        vehicle_type: session.vehicleType,
        driver_status: session.driverStatus,
      }
    : null
  const { data, isLoading, error, refresh } = useDriverPortalData(driver)

  const historyStops = useMemo(
    () => (data?.stops ?? []).filter((stop) => stop.deliveryStatus === "delivered" || stop.deliveryStatus === "failed"),
    [data?.stops],
  )

  if (!isReady || !session) {
    return null
  }

  return (
    <AppShell>
      <PageHeader title="History" subtitle="Completed and exception stops" />

      <main className="px-4 py-6 max-w-4xl mx-auto space-y-5">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Spinner className="h-8 w-8 text-[var(--muted-teal)]" />
          </div>
        ) : error ? (
          <StatePanel icon={History} title="Unable to load history" message={error} actionLabel="Retry" onAction={() => void refresh()} />
        ) : historyStops.length === 0 ? (
          <StatePanel icon={PackageCheck} title="No completed stops yet" message="Once you complete or fail a stop, it will appear here for quick review." actionLabel="Refresh" onAction={() => void refresh()} />
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-[var(--muted-teal)]/10 rounded-xl p-4 border border-[var(--muted-teal)]/20">
                <p className="text-sm text-muted-foreground">Delivered</p>
                <p className="mt-2 text-2xl font-bold text-[var(--evergreen)]">{historyStops.filter((stop) => stop.deliveryStatus === "delivered").length}</p>
              </div>
              <div className="bg-red-50 rounded-xl p-4 border border-red-200">
                <p className="text-sm text-muted-foreground">Failed</p>
                <p className="mt-2 text-2xl font-bold text-red-600">{historyStops.filter((stop) => stop.deliveryStatus === "failed").length}</p>
              </div>
            </div>

            <div className="space-y-3">
              {historyStops.map((stop) => (
                <DeliveryCard
                  key={stop.routeStopId}
                  stopNumber={stop.sequence}
                  customerName={stop.customerName}
                  address={stop.address}
                  timeWindow={formatTimeWindow(stop.estimatedArrival, stop.sequence)}
                  deliveryType={stop.deliveryType}
                  status={stop.deliveryStatus}
                  isActive={stop.deliveryStatus === "failed"}
                />
              ))}
            </div>
            <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
              <AlertTriangle className="w-4 h-4" />
              Status history is sourced from the backend tracking API.
            </div>
          </>
        )}
      </main>
    </AppShell>
  )
}
