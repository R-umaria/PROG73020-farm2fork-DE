"use client"

import { useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { Package, Search, SlidersHorizontal } from "lucide-react"

import { AppShell } from "@/components/delivery/app-shell"
import { DeliveryCard } from "@/components/delivery/delivery-card"
import { PageHeader } from "@/components/delivery/page-header"
import { StatePanel } from "@/components/delivery/state-panel"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useDriverPortalData } from "@/hooks/use-driver-portal-data"
import { useDriverSession } from "@/hooks/use-driver-session"
import { formatTimeWindow } from "@/lib/portal-formatters"

export default function DeliveriesPage() {
  const router = useRouter()
  const { session, isReady } = useDriverSession({ required: true })
  const [search, setSearch] = useState("")
  const driver = session
    ? {
        driver_id: session.driverId,
        driver_name: session.driverName,
        vehicle_type: session.vehicleType,
        driver_status: session.driverStatus,
      }
    : null
  const { data, isLoading, error, refresh } = useDriverPortalData(driver)

  const filteredStops = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()
    const stops = data?.stops ?? []
    if (!normalizedSearch) {
      return stops
    }

    return stops.filter((stop) =>
      [stop.customerName, stop.address, String(stop.orderId)].some((value) => value.toLowerCase().includes(normalizedSearch)),
    )
  }, [data?.stops, search])

  if (!isReady || !session) {
    return null
  }

  const deliveredCount = data?.stops.filter((stop) => stop.deliveryStatus === "delivered").length ?? 0
  const inTransitCount = data?.stops.filter((stop) => stop.deliveryStatus === "out_for_delivery").length ?? 0
  const scheduledCount = data?.stops.filter((stop) => stop.deliveryStatus === "scheduled").length ?? 0

  return (
    <AppShell>
      <PageHeader
        title="Deliveries"
        subtitle={`${data?.stops.length ?? 0} stops assigned`}
        actions={
          <Button variant="ghost" size="icon" className="text-white hover:bg-white/10" onClick={() => void refresh()}>
            <SlidersHorizontal className="w-5 h-5" />
          </Button>
        }
      />

      <main className="px-4 py-6 max-w-4xl mx-auto space-y-5">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            placeholder="Search deliveries..."
            className="pl-10 h-12 bg-card border-border rounded-xl"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Spinner className="h-8 w-8 text-[var(--muted-teal)]" />
          </div>
        ) : error ? (
          <StatePanel icon={Package} title="Unable to load deliveries" message={error} actionLabel="Retry" onAction={() => void refresh()} />
        ) : !data || data.stops.length === 0 ? (
          <StatePanel icon={Package} title="No deliveries assigned" message="This driver does not have any route stops yet." actionLabel="Refresh" onAction={() => void refresh()} />
        ) : (
          <>
            <div className="flex items-center gap-3">
              <div className="flex-1 bg-[var(--muted-teal)]/10 rounded-xl p-3 border border-[var(--muted-teal)]/20">
                <div className="flex items-center gap-2">
                  <Package className="w-4 h-4 text-[var(--muted-teal)]" />
                  <span className="text-sm font-medium text-foreground">{deliveredCount} Delivered</span>
                </div>
              </div>
              <div className="flex-1 bg-[var(--midnight-violet)]/10 rounded-xl p-3 border border-[var(--midnight-violet)]/20">
                <div className="flex items-center gap-2">
                  <Package className="w-4 h-4 text-[var(--midnight-violet)]" />
                  <span className="text-sm font-medium text-foreground">{inTransitCount} In Transit</span>
                </div>
              </div>
              <div className="flex-1 bg-muted rounded-xl p-3 border border-border">
                <div className="flex items-center gap-2">
                  <Package className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium text-foreground">{scheduledCount} Scheduled</span>
                </div>
              </div>
            </div>

            <section>
              <h2 className="text-sm font-medium text-muted-foreground mb-3">All Deliveries</h2>
              <div className="space-y-3">
                {filteredStops.map((stop) => (
                  <DeliveryCard
                    key={stop.routeStopId}
                    stopNumber={stop.sequence}
                    customerName={stop.customerName}
                    address={stop.address}
                    timeWindow={formatTimeWindow(stop.estimatedArrival, stop.sequence)}
                    deliveryType={stop.deliveryType}
                    status={stop.deliveryStatus}
                    isActive={stop.deliveryStatus === "out_for_delivery"}
                    onClick={() => router.push(`/deliveries/${stop.routeStopId}`)}
                  />
                ))}
              </div>
            </section>
          </>
        )}
      </main>
    </AppShell>
  )
}
