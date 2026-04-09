"use client"

import { useMemo, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  Clock,
  FileText,
  MapPin,
  Navigation,
  Package,
  Phone,
  User,
} from "lucide-react"

import { AppShell } from "@/components/delivery/app-shell"
import { PageHeader } from "@/components/delivery/page-header"
import { ProgressTimeline } from "@/components/delivery/progress-timeline"
import { StatePanel } from "@/components/delivery/state-panel"
import { StatusBadge } from "@/components/delivery/status-badge"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { useDriverPortalData } from "@/hooks/use-driver-portal-data"
import { useDriverSession } from "@/hooks/use-driver-session"
import {
  completeDelivery,
  completeRouteStop,
  failDelivery,
  startDelivery,
} from "@/lib/api-client"
import { formatShortTime, formatTimeWindow } from "@/lib/portal-formatters"

export default function DeliveryDetailPage() {
  const router = useRouter()
  const params = useParams()
  const routeStopId = params.id as string
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
  const [actionError, setActionError] = useState<string | null>(null)
  const [isMutating, setIsMutating] = useState(false)

  const stop = useMemo(
    () => data?.stops.find((candidate) => candidate.routeStopId === routeStopId) ?? null,
    [data?.stops, routeStopId],
  )

  const timelineSteps = useMemo(() => {
    const history = stop?.tracking?.status_history ?? []
    const lookup = new Map(history.map((entry) => [entry.status, entry]))

    const deliveredOrFailed = stop?.deliveryStatus === "delivered" || stop?.deliveryStatus === "failed"

    return [
      {
        label: "Scheduled",
        time: lookup.get("scheduled")?.changed_at ? formatShortTime(lookup.get("scheduled")?.changed_at) : undefined,
        status: lookup.has("scheduled") ? "completed" as const : "pending" as const,
      },
      {
        label: "Out for Delivery",
        time: lookup.get("out_for_delivery")?.changed_at ? formatShortTime(lookup.get("out_for_delivery")?.changed_at) : undefined,
        status: lookup.has("out_for_delivery")
          ? "completed" as const
          : stop?.deliveryStatus === "scheduled"
            ? "pending" as const
            : deliveredOrFailed
              ? "completed" as const
              : "current" as const,
      },
      {
        label: stop?.deliveryStatus === "failed" ? "Delivery Failed" : "Delivery Completed",
        time:
          stop?.deliveryStatus === "delivered"
            ? formatShortTime(stop?.tracking?.completed_at)
            : stop?.deliveryStatus === "failed"
              ? formatShortTime(stop?.tracking?.failed_at)
              : undefined,
        status:
          stop?.deliveryStatus === "delivered" || stop?.deliveryStatus === "failed"
            ? "completed" as const
            : stop?.deliveryStatus === "out_for_delivery"
              ? "current" as const
              : "pending" as const,
      },
    ]
  }, [stop])

  if (!isReady || !session) {
    return null
  }

  const handleStart = async () => {
    if (!stop?.deliveryExecutionId) {
      setActionError("This stop does not have a delivery execution record yet.")
      return
    }

    setActionError(null)
    setIsMutating(true)
    try {
      await startDelivery(stop.deliveryExecutionId)
      await refresh()
    } catch (caughtError) {
      setActionError(caughtError instanceof Error ? caughtError.message : "Unable to start delivery.")
    } finally {
      setIsMutating(false)
    }
  }

  const handleComplete = async () => {
    if (!stop?.deliveryExecutionId) {
      setActionError("This stop does not have a delivery execution record yet.")
      return
    }

    setActionError(null)
    setIsMutating(true)
    try {
      await completeDelivery(stop.deliveryExecutionId, {
        received_by: session.driverName,
        proof_of_delivery_url: null,
      })
      await completeRouteStop(stop.routeStopId)
      await refresh()
    } catch (caughtError) {
      setActionError(caughtError instanceof Error ? caughtError.message : "Unable to complete delivery.")
    } finally {
      setIsMutating(false)
    }
  }

  const handleFail = async () => {
    if (!stop?.deliveryExecutionId) {
      setActionError("This stop does not have a delivery execution record yet.")
      return
    }

    const description = window.prompt("Add a short reason for the failed delivery:", "Customer unavailable")
    if (!description) {
      return
    }

    setActionError(null)
    setIsMutating(true)
    try {
      await failDelivery(stop.deliveryExecutionId, {
        exception_type: "delivery_failed",
        description,
        retry_allowed: true,
      })
      await refresh()
    } catch (caughtError) {
      setActionError(caughtError instanceof Error ? caughtError.message : "Unable to update delivery status.")
    } finally {
      setIsMutating(false)
    }
  }

  return (
    <AppShell>
      <PageHeader title={stop ? `Stop #${stop.sequence}` : "Delivery Detail"} subtitle={stop?.customerName ?? "Loading stop"} backHref="/dashboard" />

      <main className="px-4 py-6 max-w-4xl mx-auto space-y-5">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Spinner className="h-8 w-8 text-[var(--muted-teal)]" />
          </div>
        ) : error ? (
          <StatePanel icon={Package} title="Unable to load stop detail" message={error} actionLabel="Retry" onAction={() => void refresh()} />
        ) : !stop ? (
          <StatePanel icon={Package} title="Stop not found" message="This stop is not part of the current driver schedule." actionLabel="Back to deliveries" onAction={() => router.push("/deliveries")} />
        ) : (
          <>
            <div className="flex items-center justify-between bg-card rounded-xl p-4 border border-border">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-[var(--muted-teal)]/10">
                  <Package className="w-6 h-6 text-[var(--muted-teal)]" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Order ID</p>
                  <p className="font-semibold text-foreground">#{stop.orderId}</p>
                </div>
              </div>
              <StatusBadge status={stop.deliveryStatus} />
            </div>

            <div className="bg-card rounded-xl p-5 border border-border space-y-4">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-[var(--twilight-indigo)]/10">
                  <User className="w-5 h-5 text-[var(--twilight-indigo)]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-muted-foreground">Customer</p>
                  <p className="font-semibold text-foreground text-lg">{stop.customerName}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-[var(--muted-teal)]/10">
                  <MapPin className="w-5 h-5 text-[var(--muted-teal)]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-muted-foreground">Delivery Address</p>
                  <p className="font-medium text-foreground">{stop.address}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-[var(--midnight-violet)]/10">
                  <Phone className="w-5 h-5 text-[var(--midnight-violet)]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-muted-foreground">Contact</p>
                  {stop.phoneNumber ? (
                    <a href={`tel:${stop.phoneNumber}`} className="font-medium text-[var(--twilight-indigo)] hover:underline">
                      {stop.phoneNumber}
                    </a>
                  ) : (
                    <p className="font-medium text-muted-foreground">Phone not available in customer enrichment yet</p>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-[var(--thistle)]">
                  <Clock className="w-5 h-5 text-[var(--twilight-indigo)]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-muted-foreground">Delivery Window</p>
                  <p className="font-medium text-foreground">{formatTimeWindow(stop.estimatedArrival, stop.sequence)}</p>
                </div>
              </div>
            </div>

            <div className="bg-[var(--thistle)]/30 rounded-xl p-4 border border-[var(--thistle)]">
              <div className="flex items-start gap-3">
                <FileText className="w-5 h-5 text-[var(--twilight-indigo)] flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-[var(--twilight-indigo)]">Delivery Notes</p>
                  <p className="text-sm text-foreground mt-1">{stop.itemSummary}</p>
                </div>
              </div>
            </div>

            <div className="bg-card rounded-xl p-5 border border-border">
              <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                <Package className="w-5 h-5 text-muted-foreground" />
                Items ({stop.deliveryRecord?.items.length ?? 0})
              </h3>
              {stop.deliveryRecord?.items.length ? (
                <ul className="space-y-2">
                  {stop.deliveryRecord.items.map((item) => (
                    <li key={`${item.external_item_id}-${item.item_name}`} className="flex items-center gap-3 text-sm">
                      <div className="w-1.5 h-1.5 rounded-full bg-[var(--muted-teal)]" />
                      <span className="text-foreground">{item.item_name} ({item.quantity})</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">No item details are stored for this stop yet.</p>
              )}
            </div>

            <div className="bg-card rounded-xl p-5 border border-border">
              <h3 className="font-semibold text-foreground mb-4">Delivery Progress</h3>
              <ProgressTimeline steps={timelineSteps} />
            </div>

            {stop.deliveryStatus === "delivered" ? (
              <div className="bg-[var(--muted-teal)]/10 rounded-xl p-4 border border-[var(--muted-teal)]/30">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-[var(--muted-teal)]/20">
                    <Camera className="w-5 h-5 text-[var(--muted-teal)]" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-[var(--evergreen)]">Completed in backend</p>
                    <p className="text-xs text-muted-foreground">Last status update at {formatShortTime(stop.tracking?.completed_at)}</p>
                  </div>
                  <CheckCircle2 className="w-5 h-5 text-[var(--muted-teal)]" />
                </div>
              </div>
            ) : null}

            {actionError ? <p className="text-sm text-red-600">{actionError}</p> : null}

            <div className="space-y-3 pt-2">
              {stop.deliveryStatus === "scheduled" ? (
                <Button onClick={() => void handleStart()} disabled={isMutating} className="w-full h-14 bg-[var(--muted-teal)] hover:bg-[var(--muted-teal)]/90 text-[var(--evergreen)] font-semibold text-base rounded-xl shadow-lg shadow-[var(--muted-teal)]/20">
                  {isMutating ? <Spinner className="h-5 w-5" /> : <Navigation className="w-5 h-5 mr-2" />}
                  Start Delivery
                </Button>
              ) : null}

              {stop.deliveryStatus === "out_for_delivery" ? (
                <Button onClick={() => void handleComplete()} disabled={isMutating} className="w-full h-14 bg-[var(--muted-teal)] hover:bg-[var(--muted-teal)]/90 text-[var(--evergreen)] font-semibold text-base rounded-xl shadow-lg shadow-[var(--muted-teal)]/20">
                  {isMutating ? <Spinner className="h-5 w-5" /> : <CheckCircle2 className="w-5 h-5 mr-2" />}
                  Complete Delivery
                </Button>
              ) : null}

              {stop.deliveryStatus !== "delivered" && stop.deliveryStatus !== "failed" ? (
                <Button onClick={() => void handleFail()} disabled={isMutating} variant="outline" className="w-full h-12 border-red-200 text-red-600 hover:bg-red-50 font-medium rounded-xl">
                  <AlertTriangle className="w-5 h-5 mr-2" />
                  Report Delivery Issue
                </Button>
              ) : null}

              <Button onClick={() => router.push("/summary")} variant="outline" className="w-full h-12 border-border text-foreground font-medium rounded-xl">
                View Shift Summary
              </Button>
            </div>
          </>
        )}
      </main>
    </AppShell>
  )
}
