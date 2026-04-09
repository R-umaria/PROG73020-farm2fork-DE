"use client"

import { useMemo } from "react"
import { useRouter } from "next/navigation"
import { AlertTriangle, ArrowRight, Award, CheckCircle2, Clock, Home, Truck } from "lucide-react"

import { AppShell } from "@/components/delivery/app-shell"
import { StatePanel } from "@/components/delivery/state-panel"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { useDriverPortalData } from "@/hooks/use-driver-portal-data"
import { useDriverSession } from "@/hooks/use-driver-session"
import { formatRouteLabel } from "@/lib/portal-formatters"

export default function ShiftSummaryPage() {
  const router = useRouter()
  const { session, isReady, signOut } = useDriverSession({ required: true })
  const driver = session
    ? {
        driver_id: session.driverId,
        driver_name: session.driverName,
        vehicle_type: session.vehicleType,
        driver_status: session.driverStatus,
      }
    : null
  const { data, isLoading, error, refresh } = useDriverPortalData(driver)

  const stats = useMemo(() => {
    const stops = data?.stops ?? []
    return {
      completed: stops.filter((stop) => stop.deliveryStatus === "delivered").length,
      failed: stops.filter((stop) => stop.deliveryStatus === "failed").length,
      pending: stops.filter((stop) => stop.deliveryStatus === "scheduled" || stop.deliveryStatus === "out_for_delivery").length,
      total: stops.length,
      routeLabel: formatRouteLabel(stops[0]?.routeGroupId),
    }
  }, [data?.stops])

  if (!isReady || !session) {
    return null
  }

  return (
    <AppShell showNav={false}>
      <div className="bg-gradient-to-b from-[var(--evergreen)] to-[#1a3a20] px-6 pt-16 pb-12 text-center">
        <div className="w-20 h-20 rounded-full bg-[var(--muted-teal)]/20 border-2 border-[var(--muted-teal)] mx-auto mb-6 flex items-center justify-center">
          <Award className="w-10 h-10 text-[var(--muted-teal)]" />
        </div>
        <h1 className="text-2xl font-bold text-white">Shift Summary</h1>
        <p className="text-white/70 mt-2">Live route progress for {session.driverName}</p>
      </div>

      <main className="px-4 py-6 max-w-lg mx-auto -mt-6 space-y-5">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Spinner className="h-8 w-8 text-[var(--muted-teal)]" />
          </div>
        ) : error ? (
          <StatePanel icon={AlertTriangle} title="Unable to load summary" message={error} actionLabel="Retry" onAction={() => void refresh()} />
        ) : !data ? (
          <StatePanel icon={Truck} title="No shift data yet" message="Route summary will appear after a route is assigned." actionLabel="Back to dashboard" onAction={() => router.push("/dashboard")} />
        ) : (
          <>
            <div className="bg-card rounded-2xl p-6 shadow-lg border border-border">
              <h2 className="text-sm font-medium text-muted-foreground mb-4">Shift Summary</h2>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[var(--muted-teal)]/10 rounded-xl p-4 border border-[var(--muted-teal)]/20">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle2 className="w-5 h-5 text-[var(--muted-teal)]" />
                    <span className="text-sm text-muted-foreground">Completed</span>
                  </div>
                  <p className="text-3xl font-bold text-[var(--evergreen)]">{stats.completed}</p>
                  <p className="text-xs text-muted-foreground">deliveries</p>
                </div>

                <div className="bg-red-50 rounded-xl p-4 border border-red-200">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="w-5 h-5 text-red-500" />
                    <span className="text-sm text-muted-foreground">Exceptions</span>
                  </div>
                  <p className="text-3xl font-bold text-red-600">{stats.failed}</p>
                  <p className="text-xs text-muted-foreground">reported</p>
                </div>

                <div className="bg-[var(--twilight-indigo)]/10 rounded-xl p-4 border border-[var(--twilight-indigo)]/20">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="w-5 h-5 text-[var(--twilight-indigo)]" />
                    <span className="text-sm text-muted-foreground">Pending</span>
                  </div>
                  <p className="text-3xl font-bold text-[var(--twilight-indigo)]">{stats.pending}</p>
                  <p className="text-xs text-muted-foreground">remaining stops</p>
                </div>

                <div className="bg-[var(--thistle)]/30 rounded-xl p-4 border border-[var(--thistle)]">
                  <div className="flex items-center gap-2 mb-2">
                    <Truck className="w-5 h-5 text-[var(--midnight-violet)]" />
                    <span className="text-sm text-muted-foreground">Route</span>
                  </div>
                  <p className="text-lg font-bold text-[var(--midnight-violet)]">{stats.routeLabel}</p>
                  <p className="text-xs text-muted-foreground">{stats.total} assigned stops</p>
                </div>
              </div>
            </div>

            <div className="bg-card rounded-xl p-5 border border-border">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-foreground">Route Completion</span>
                <span className="text-sm font-bold text-[var(--muted-teal)]">{stats.total === 0 ? 0 : Math.round((stats.completed / stats.total) * 100)}%</span>
              </div>
              <div className="h-3 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-[var(--muted-teal)] rounded-full" style={{ width: `${stats.total === 0 ? 0 : (stats.completed / stats.total) * 100}%` }} />
              </div>
              <div className="flex items-center justify-between mt-3 text-xs text-muted-foreground">
                <span>Driver #{session.driverId}</span>
                <span>{session.vehicleType}</span>
              </div>
            </div>

            <div className="space-y-3 pt-4">
              <Button onClick={() => router.push("/dashboard")} className="w-full h-14 bg-[var(--evergreen)] hover:bg-[var(--evergreen)]/90 text-white font-semibold rounded-xl">
                <Home className="w-5 h-5 mr-2" />
                Return to Dashboard
              </Button>

              <Button onClick={signOut} variant="outline" className="w-full h-14 border-border text-foreground font-semibold rounded-xl">
                End Shift
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </div>
          </>
        )}
      </main>
    </AppShell>
  )
}
