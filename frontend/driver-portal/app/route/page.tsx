"use client"

import { useMemo } from "react"
import { useRouter } from "next/navigation"
import { ChevronRight, MapPin, Navigation, Route, Truck, User } from "lucide-react"

import { AppShell } from "@/components/delivery/app-shell"
import { DeliveryCard } from "@/components/delivery/delivery-card"
import { PageHeader } from "@/components/delivery/page-header"
import { RouteMap } from "@/components/delivery/route-map"
import { StatePanel } from "@/components/delivery/state-panel"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { useDriverPortalData } from "@/hooks/use-driver-portal-data"
import { useDriverSession } from "@/hooks/use-driver-session"
import { formatRouteLabel, formatShortTime, formatTimeWindow } from "@/lib/portal-formatters"

export default function RouteOverviewPage() {
  const router = useRouter()
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

  const routeStops = useMemo(
    () =>
      (data?.stops ?? []).map((stop) => ({
        id: stop.routeStopId,
        name: stop.customerName,
        status: stop.deliveryStatus,
      })),
    [data?.stops],
  )

  if (!isReady || !session) {
    return null
  }

  const firstStop = data?.stops[0] ?? null
  const lastStop = data?.stops.length ? data.stops[data.stops.length - 1] : null

  return (
    <AppShell>
      <PageHeader title="Route Overview" subtitle={formatRouteLabel(firstStop?.routeGroupId)} backHref="/dashboard" />

      <main className="px-4 py-6 max-w-4xl mx-auto space-y-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Spinner className="h-8 w-8 text-[var(--muted-teal)]" />
          </div>
        ) : error ? (
          <StatePanel icon={Route} title="Unable to load route data" message={error} actionLabel="Retry" onAction={() => void refresh()} />
        ) : !data || data.stops.length === 0 ? (
          <StatePanel icon={Route} title="No route planned yet" message="Once planning assigns route stops to this driver, the route overview will appear here." actionLabel="Refresh" onAction={() => void refresh()} />
        ) : (
          <>
            <RouteMap stops={routeStops} className="h-[220px]" />

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-card rounded-xl p-4 border border-border">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-[var(--muted-teal)]/10">
                    <Route className="w-5 h-5 text-[var(--muted-teal)]" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Route ID</p>
                    <p className="font-semibold text-foreground">{formatRouteLabel(firstStop?.routeGroupId)}</p>
                  </div>
                </div>
              </div>

              <div className="bg-card rounded-xl p-4 border border-border">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-[var(--twilight-indigo)]/10">
                    <MapPin className="w-5 h-5 text-[var(--twilight-indigo)]" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">First ETA</p>
                    <p className="font-semibold text-foreground">{formatShortTime(firstStop?.estimatedArrival)}</p>
                  </div>
                </div>
              </div>

              <div className="bg-card rounded-xl p-4 border border-border">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-[var(--midnight-violet)]/10">
                    <User className="w-5 h-5 text-[var(--midnight-violet)]" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Driver</p>
                    <p className="font-semibold text-foreground">{data.driver.driver_name}</p>
                  </div>
                </div>
              </div>

              <div className="bg-card rounded-xl p-4 border border-border">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-[var(--thistle)]">
                    <Truck className="w-5 h-5 text-[var(--twilight-indigo)]" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Vehicle</p>
                    <p className="font-semibold text-foreground">{data.driver.vehicle_type}</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-card rounded-xl p-5 border border-border">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm text-muted-foreground">Route progress</p>
                  <p className="text-lg font-semibold text-foreground">{data.stops.filter((stop) => stop.deliveryStatus === "delivered").length} / {data.stops.length} completed</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Last ETA</p>
                  <p className="font-semibold text-foreground">{formatShortTime(lastStop?.estimatedArrival)}</p>
                </div>
              </div>
            </div>

            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-foreground">Planned Stops</h2>
                <Button onClick={() => router.push(`/deliveries/${firstStop?.routeStopId}`)} className="bg-[var(--evergreen)] hover:bg-[var(--evergreen)]/90 text-white">
                  Open Next Stop
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
              <div className="space-y-3">
                {data.stops.map((stop) => (
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

            <div className="flex items-center justify-center text-xs text-muted-foreground gap-2">
              <Navigation className="w-4 h-4" />
              Live route data is coming from the backend planning and driver APIs.
            </div>
          </>
        )}
      </main>
    </AppShell>
  )
}
