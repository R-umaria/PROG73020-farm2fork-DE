"use client"

import { useMemo } from "react"
import { useRouter } from "next/navigation"
import { CheckCircle2, ChevronRight, Clock, MapPin, Package, Play, Timer } from "lucide-react"

import { AppShell } from "@/components/delivery/app-shell"
import { DeliveryCard } from "@/components/delivery/delivery-card"
import { MetricCard } from "@/components/delivery/metric-card"
import { PageHeader } from "@/components/delivery/page-header"
import { StatePanel } from "@/components/delivery/state-panel"
import { StatusBadge } from "@/components/delivery/status-badge"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { useDriverPortalData } from "@/hooks/use-driver-portal-data"
import { useDriverSession } from "@/hooks/use-driver-session"
import { formatLongDate, formatRouteLabel, formatShortTime, formatTimeWindow } from "@/lib/portal-formatters"

export default function DashboardPage() {
  const router = useRouter()
  const { session, isReady } = useDriverSession({ required: true, requireShift: true })
  const driver = session
    ? {
        driver_id: session.driverId,
        driver_name: session.driverName,
        vehicle_type: session.vehicleType,
        driver_status: session.driverStatus,
      }
    : null
  const { data, isLoading, error, refresh } = useDriverPortalData(driver, session?.selectedShiftId)

  const stats = useMemo(() => {
    const stops = data?.stops ?? []
    const completed = stops.filter((stop) => stop.deliveryStatus === "delivered").length
    const active = stops.find((stop) => stop.deliveryStatus === "out_for_delivery")
    const nextStop = active ?? stops.find((stop) => stop.deliveryStatus === "scheduled") ?? null
    const remaining = stops.filter((stop) => stop.deliveryStatus !== "delivered").length
    return { stops, completed, remaining, nextStop, active }
  }, [data])

  if (!isReady || !session) {
    return null
  }

  return (
    <AppShell>
      <PageHeader
        title={`Good ${new Date().getHours() < 12 ? "morning" : "afternoon"}, ${session.driverName.split(" ")[0]}`}
        subtitle={`${formatLongDate(new Date())} • ${session.selectedShiftName ?? "Active shift"}`}
        showNotifications
      />

      <main className="px-4 py-6 max-w-4xl mx-auto space-y-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Spinner className="h-8 w-8 text-[var(--muted-teal)]" />
          </div>
        ) : error ? (
          <StatePanel
            icon={Package}
            title="Unable to load your live schedule"
            message={error}
            actionLabel="Retry"
            onAction={() => void refresh()}
          />
        ) : !data || stats.stops.length === 0 ? (
          <StatePanel
            icon={Package}
            title="No route assigned yet"
            message="This driver does not have any scheduled route stops right now. Once planning assigns a route group, it will show here automatically."
            actionLabel="Refresh"
            onAction={() => void refresh()}
          />
        ) : (
          <>
            <div className="bg-[var(--midnight-violet)] rounded-2xl p-4 text-white">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <StatusBadge status={stats.active ? "out_for_delivery" : stats.remaining === 0 ? "delivered" : "scheduled"} />
                  </div>
                  <p className="text-sm text-white/70 mt-2">
                    {formatRouteLabel(stats.stops[0]?.routeGroupId)} • {data.driver.vehicle_type}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold">{stats.completed} of {stats.stops.length}</p>
                  <p className="text-xs text-white/60">stops completed</p>
                </div>
              </div>

              <div className="mt-4">
                <div className="h-2 bg-white/20 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[var(--muted-teal)] rounded-full transition-all duration-500"
                    style={{ width: `${(stats.completed / stats.stops.length) * 100}%` }}
                  />
                </div>
                <p className="text-xs text-white/60 mt-2">
                  Next ETA: {formatShortTime(stats.nextStop?.estimatedArrival)}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <MetricCard title="Total Deliveries" value={stats.stops.length} subtitle="assigned today" icon={Package} variant="default" />
              <MetricCard title="Delivered" value={stats.completed} subtitle={`${Math.round((stats.completed / stats.stops.length) * 100)}% done`} icon={CheckCircle2} variant="primary" />
              <MetricCard title="Scheduled" value={stats.remaining} subtitle="remaining" icon={Clock} variant="muted" />
              <MetricCard
                title="Next ETA"
                value={formatShortTime(stats.nextStop?.estimatedArrival)}
                subtitle={stats.nextStop ? `Stop #${stats.nextStop.sequence}` : "All complete"}
                icon={Timer}
                variant="accent"
              />
            </div>

            {stats.nextStop ? (
              <Button
                onClick={() => router.push(`/deliveries/${stats.nextStop?.routeStopId}`)}
                className="w-full h-14 bg-[var(--muted-teal)] hover:bg-[var(--muted-teal)]/90 text-[var(--evergreen)] font-semibold text-base rounded-xl shadow-lg shadow-[var(--muted-teal)]/20"
              >
                <Play className="w-5 h-5 mr-2" />
                {stats.active ? "Continue Delivery" : "Open Next Stop"}
                <ChevronRight className="w-5 h-5 ml-auto" />
              </Button>
            ) : (
              <Button
                onClick={() => router.push("/summary")}
                className="w-full h-14 bg-[var(--muted-teal)] hover:bg-[var(--muted-teal)]/90 text-[var(--evergreen)] font-semibold text-base rounded-xl shadow-lg shadow-[var(--muted-teal)]/20"
              >
                View Shift Summary
                <ChevronRight className="w-5 h-5 ml-auto" />
              </Button>
            )}

            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-foreground">Today&apos;s Schedule</h2>
                <button
                  onClick={() => router.push("/route")}
                  className="text-sm font-medium text-[var(--twilight-indigo)] flex items-center gap-1 hover:text-[var(--midnight-violet)] transition-colors"
                >
                  View Route
                  <MapPin className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-3">
                {stats.stops.map((stop) => (
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
