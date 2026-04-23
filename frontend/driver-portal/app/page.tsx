"use client"

import Image from "next/image"
import { Suspense, useCallback, useEffect, useMemo, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { ArrowRight, LockKeyhole, LogOut, MapPin, Route, UserRound, Warehouse } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import {
  listAvailableShifts,
  resolveDriverSession,
  seedDemoData,
  startShift,
  type AvailableShift,
} from "@/lib/api-client"
import {
  clearDriverSession,
  getDriverSession,
  saveDriverSession,
  updateSelectedShift,
  type DriverSession,
} from "@/lib/driver-session"

const demoDrivers = [
  { email: "driver.demo@farm2fork.local", label: "Jordan Lee" },
  { email: "driver.sam@farm2fork.local", label: "Sam Patel" },
  { email: "driver.avery@farm2fork.local", label: "Avery Chen" },
]

const formatDateTime = (value: string | null) => {
  if (!value) return "TBD"
  return new Date(value).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

const formatDistance = (value: number | null) => (value ? `${value.toFixed(1)} km` : "Pending")
const formatDuration = (value: number | null) => (value ? `${value} min` : "Pending")

function buildUnsignedJwt(email: string): string {
  const encode = (payload: unknown) =>
    btoa(JSON.stringify(payload)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "")
  const now = Math.floor(Date.now() / 1000)
  return `${encode({ alg: "none", typ: "JWT" })}.${encode({ email, user_type: "driver", exp: now + 60 * 60 * 8 })}.`
}

function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-[rgba(0,0,0,0.15)] px-4 py-3 backdrop-blur-sm">
      <p className="text-[11px] uppercase tracking-[0.18em] text-white/45">{label}</p>
      <p className="mt-2 text-base font-semibold text-white">{value}</p>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-white/8 py-3 last:border-b-0 last:pb-0">
      <span className="text-sm text-white/55">{label}</span>
      <span className="text-sm font-medium text-white">{value}</span>
    </div>
  )
}

function ShiftCard({
  shift,
  onStart,
  isStarting,
}: {
  shift: AvailableShift
  onStart: (shift: AvailableShift) => void
  isStarting: boolean
}) {
  return (
    <article className="rounded-[28px] border border-white/10 bg-[rgba(0,0,0,0.15)] p-6 shadow-[0_24px_60px_rgba(0,0,0,0.18)] backdrop-blur-sm">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-[var(--muted-teal)]/15 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-[var(--muted-teal)]">
              {shift.zone_code}
            </span>
            <span className="rounded-full border border-white/10 bg-[rgba(255,255,255,0.08)] px-3 py-1 text-xs text-white/75">
              {shift.total_stops} stops
            </span>
          </div>
          <h3 className="mt-4 text-2xl font-semibold text-white">{shift.shift_name}</h3>
          <div className="mt-3 flex items-start gap-2 text-sm text-white/70">
            <Warehouse className="mt-0.5 h-4 w-4 shrink-0 text-[var(--muted-teal)]" />
            <span>
              {shift.warehouse_name} • {shift.warehouse_address}
            </span>
          </div>
          {shift.stop_preview.length > 0 ? (
            <div className="mt-3 flex items-start gap-2 text-sm text-white/60">
              <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-[var(--muted-teal)]" />
              <span>{shift.stop_preview.join(" • ")}</span>
            </div>
          ) : null}
        </div>

        <Button
          type="button"
          onClick={() => onStart(shift)}
          disabled={isStarting}
          className="h-12 min-w-[184px] rounded-2xl bg-[var(--muted-teal)] text-[var(--evergreen)] hover:bg-[var(--muted-teal)]/90"
        >
          {isStarting ? <Spinner className="h-4 w-4" /> : <LockKeyhole className="h-4 w-4" />}
          {isStarting ? "Starting..." : "Start shift"}
        </Button>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatPill label="Planned dispatch" value={formatDateTime(shift.scheduled_date)} />
        <StatPill label="Trip time" value={formatDuration(shift.estimated_duration_min)} />
        <StatPill label="Distance" value={formatDistance(shift.estimated_distance_km)} />
        <StatPill label="ETA window" value={`${formatDateTime(shift.first_eta)} → ${formatDateTime(shift.last_eta)}`} />
      </div>
    </article>
  )
}

function ShiftSelectionScreen() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get("token")

  const [session, setSession] = useState<DriverSession | null>(() => getDriverSession())
  const [shifts, setShifts] = useState<AvailableShift[]>([])
  const [isBootstrapping, setIsBootstrapping] = useState(false)
  const [isLoadingShifts, setIsLoadingShifts] = useState(false)
  const [isSeedingDemo, setIsSeedingDemo] = useState(false)
  const [startingShiftId, setStartingShiftId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadShifts = useCallback(async () => {
    setIsLoadingShifts(true)
    setError(null)
    try {
      const payload = await listAvailableShifts()
      setShifts(payload)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load available shifts.")
    } finally {
      setIsLoadingShifts(false)
    }
  }, [])

  useEffect(() => {
    const active = getDriverSession()
    setSession(active)

    if (active?.selectedShiftId) {
      router.replace("/dashboard")
      return
    }

    if (!token) return

    let cancelled = false
    setIsBootstrapping(true)
    setError(null)

    void resolveDriverSession(token)
      .then((payload) => {
        if (cancelled) return

        const nextSession: DriverSession = {
          email: payload.email,
          driverId: payload.driver_id,
          driverName: payload.driver_name,
          vehicleType: payload.vehicle_type,
          driverStatus: payload.driver_status,
          signedInAt: new Date().toISOString(),
          selectedShiftId: payload.active_route_group_id ?? null,
          selectedShiftName: payload.active_route_group_name ?? null,
          selectedZoneCode: payload.active_zone_code ?? null,
        }

        saveDriverSession(nextSession, false)
        setSession(nextSession)
        router.replace(nextSession.selectedShiftId ? "/dashboard" : "/")
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Unable to establish driver session.")
      })
      .finally(() => {
        if (!cancelled) setIsBootstrapping(false)
      })

    return () => {
      cancelled = true
    }
  }, [router, token])

  useEffect(() => {
    if (!session || session.selectedShiftId) return
    void loadShifts()
  }, [loadShifts, session])

  const sortedShifts = useMemo(
    () => [...shifts].sort((a, b) => new Date(a.scheduled_date).getTime() - new Date(b.scheduled_date).getTime()),
    [shifts],
  )

  const summary = useMemo(() => {
    const totalStops = sortedShifts.reduce((sum, shift) => sum + shift.total_stops, 0)
    const totalDistance = sortedShifts.reduce((sum, shift) => sum + (shift.estimated_distance_km ?? 0), 0)
    const totalMinutes = sortedShifts.reduce((sum, shift) => sum + (shift.estimated_duration_min ?? 0), 0)
    return {
      totalStops,
      totalDistance,
      totalMinutes,
    }
  }, [sortedShifts])

  const handleStartShift = async (shift: AvailableShift) => {
    if (!session) {
      setError("A valid driver sign-in is required before you can claim a shift.")
      return
    }

    setStartingShiftId(shift.route_group_id)
    setError(null)

    try {
      await startShift(shift.route_group_id, session.driverId)
      const next = updateSelectedShift({
        shiftId: shift.route_group_id,
        shiftName: shift.shift_name,
        zoneCode: shift.zone_code,
      })
      if (next) setSession(next)
      router.push("/dashboard")
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to start shift.")
      await loadShifts().catch(() => null)
    } finally {
      setStartingShiftId(null)
    }
  }

  const handleDemoLaunch = async (email: string) => {
    setIsSeedingDemo(true)
    setError(null)

    try {
      await seedDemoData()
      window.location.href = `/?token=${encodeURIComponent(buildUnsignedJwt(email))}`
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to seed demo data.")
      setIsSeedingDemo(false)
    }
  }

  const handleSignOut = () => {
    clearDriverSession()
    setSession(null)
    setShifts([])
    setError(null)

    if (typeof window !== "undefined") {
      window.history.replaceState({}, "", "/")
      window.location.replace("/")
      return
    }

    router.replace("/")
  }

  return (
    <div className="min-h-screen overflow-x-hidden bg-[radial-gradient(circle_at_top,rgba(131,182,146,0.22),transparent_28%),linear-gradient(180deg,#14311c_0%,#102415_48%,#0b180f_100%)] text-white">
      <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:px-8 lg:py-8">
        <header className="rounded-[30px] border border-white/10 bg-[rgba(255,255,255,0.07)] px-4 py-4 shadow-[0_24px_80px_rgba(0,0,0,0.18)] backdrop-blur-md sm:px-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/45 bg-[linear-gradient(180deg,rgba(255,255,255,0.9),rgba(255,255,255,0.68))] shadow-[inset_0_1px_0_rgba(255,255,255,0.75),0_18px_40px_rgba(8,20,12,0.18)] backdrop-blur-xl">
                <Image src="/branding/logo-mark.png" alt="Farm2Fork" width={52} height={52} className="h-12 w-auto" priority />
              </div>
              <div>
                <p className="text-sm font-bold uppercase tracking-[0.18em]">
                  <span className="text-[var(--muted-teal)]">Farm</span>
                  <span className="text-[1.21em] leading-none text-[#B78517]">2</span>
                  <span className="text-[var(--muted-teal)]">Fork</span>
                </p>
                <h1 className="mt-1 text-2xl font-semibold text-white">Driver Portal</h1>
                <p className="mt-1 text-sm text-white/60">
                  {session ? "Available shifts and driver account details." : "Sign in to continue."}
                </p>
              </div>
            </div>

            {session ? (
              <Button
                type="button"
                onClick={handleSignOut}
                variant="outline"
                className="h-11 rounded-full border-white/12 bg-white/10 px-4 text-white hover:bg-white/15 hover:text-white shadow-none"
              >
                <LogOut className="h-4 w-4" />
                Log out
              </Button>
            ) : null}
          </div>
        </header>

        {!session ? (
          <section className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <div className="rounded-[34px] border border-white/10 bg-[rgba(255,255,255,0.07)] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.18)] backdrop-blur-md sm:p-8">
              <p className="text-sm uppercase tracking-[0.18em] text-[var(--muted-teal)]">Welcome</p>
              <h2 className="mt-3 text-4xl font-bold tracking-tight text-white sm:text-5xl">
                <span className="text-[var(--muted-teal)]">Farm</span>
                  <span className="text-[1.21em] leading-none text-[#B78517]">2</span>
                  <span className="text-[var(--muted-teal)]">Fork </span>
                   delivery operations
              </h2>
              <p className="mt-4 max-w-2xl text-base leading-7 text-white/72 sm:text-lg">
                Sign in with your driver account to view and claim available shifts.
              </p>

              <div className="mt-8 grid gap-3 sm:grid-cols-3">
                <StatPill label="Status" value={isBootstrapping ? "Signing in..." : "Waiting for sign-in"} />
                <StatPill label="Portal" value="Driver access" />
                <StatPill label="Shifts" value="Available after sign-in" />
              </div>

              <div className="mt-8 rounded-[28px] border border-white/10 bg-[rgba(0,0,0,0.15)] p-6">
                <h3 className="text-xl font-semibold text-white">Local demo access</h3>
                <p className="mt-3 text-sm leading-6 text-white/70">
                  Use a demo driver account to preview the portal locally while the shared sign-in flow is not connected.
                </p>
                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  {demoDrivers.map((driver) => (
                    <Button
                      key={driver.email}
                      type="button"
                      onClick={() => void handleDemoLaunch(driver.email)}
                      disabled={isSeedingDemo || isBootstrapping}
                      className="h-12 rounded-2xl bg-[var(--muted-teal)] text-[var(--evergreen)] hover:bg-[var(--muted-teal)]/90"
                    >
                      {isSeedingDemo ? <Spinner className="h-4 w-4" /> : <UserRound className="h-4 w-4" />}
                      {isSeedingDemo ? "Preparing..." : driver.label}
                    </Button>
                  ))}
                </div>
              </div>
            </div>

            <aside className="rounded-[34px] border border-white/10 bg-[rgba(255,255,255,0.07)] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.18)] backdrop-blur-md sm:p-8">
              <h3 className="text-xl font-semibold text-white">Access</h3>
              <div className="mt-4 rounded-[24px] border border-white/10 bg-[rgba(0,0,0,0.15)] p-5">
                <InfoRow label="Portal" value="Farm2Fork Driver" />
                <InfoRow label="Account" value="Driver sign-in required" />
                <InfoRow label="Route access" value="Assigned after sign-in" />
              </div>
            </aside>
          </section>
        ) : (
          <section className="mt-6 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
            <aside className="rounded-[34px] border border-white/10 bg-[rgba(255,255,255,0.07)] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.18)] backdrop-blur-md sm:p-8">
              <p className="text-sm uppercase tracking-[0.18em] text-[var(--muted-teal)]">Driver account</p>
              <h2 className="mt-3 text-3xl font-bold tracking-tight text-white">{session.driverName}</h2>
              <p className="mt-2 text-sm text-white/65">Signed in to Farm2Fork Driver Portal</p>

              <div className="mt-6 rounded-[28px] border border-white/10 bg-[rgba(0,0,0,0.15)] p-5">
                <InfoRow label="Driver ID" value={`${session.driverId}`} />
                <InfoRow label="Email" value={session.email} />
                <InfoRow label="Vehicle" value={session.vehicleType} />
                <InfoRow label="Status" value={session.driverStatus} />
              </div>

              <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
                <StatPill label="Available shifts" value={`${sortedShifts.length}`} />
                <StatPill label="Total stops" value={`${summary.totalStops}`} />
                <StatPill
                  label="Distance"
                  value={summary.totalDistance > 0 ? `${summary.totalDistance.toFixed(1)} km` : "Pending"}
                />
                <StatPill
                  label="Planned time"
                  value={summary.totalMinutes > 0 ? `${summary.totalMinutes} min` : "Pending"}
                />
              </div>
            </aside>

            <div className="rounded-[34px] border border-white/10 bg-[rgba(255,255,255,0.07)] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.18)] backdrop-blur-md sm:p-8">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-sm uppercase tracking-[0.18em] text-[var(--muted-teal)]">Shift selection</p>
                  <h2 className="mt-2 text-4xl font-bold tracking-tight text-white">Available shifts</h2>
                  <p className="mt-3 max-w-2xl text-base leading-7 text-white/72">
                    Select a shift to continue into the delivery dashboard.
                  </p>
                </div>

                <Button
                  type="button"
                  onClick={() => void loadShifts()}
                  variant="outline"
                  className="h-11 rounded-full border-white/12 bg-white/10 px-4 text-white hover:bg-white/15 hover:text-white shadow-none"
                >
                  <ArrowRight className="h-4 w-4 rotate-[-45deg]" />
                  Refresh shifts
                </Button>
              </div>

              <div className="mt-8 flex items-center gap-2 text-[var(--muted-teal)]">
                <Route className="h-5 w-5" />
                <p className="text-sm font-medium uppercase tracking-[0.16em]">{sortedShifts.length} shift{sortedShifts.length === 1 ? "" : "s"} available</p>
              </div>

              <div className="mt-6 space-y-4">
                {isLoadingShifts ? (
                  <div className="flex items-center justify-center rounded-[28px] border border-white/10 bg-[rgba(0,0,0,0.15)] py-16">
                    <Spinner className="h-8 w-8 text-[var(--muted-teal)]" />
                  </div>
                ) : sortedShifts.length === 0 ? (
                  <div className="rounded-[28px] border border-white/10 bg-[rgba(0,0,0,0.15)] p-6">
                    <h3 className="text-xl font-semibold text-white">No shifts available right now.</h3>
                    <p className="mt-3 max-w-2xl text-sm leading-6 text-white/70">
                      Check again after dispatch publishes the next route group.
                    </p>
                  </div>
                ) : (
                  sortedShifts.map((shift) => (
                    <ShiftCard
                      key={shift.route_group_id}
                      shift={shift}
                      onStart={handleStartShift}
                      isStarting={startingShiftId === shift.route_group_id}
                    />
                  ))
                )}
              </div>
            </div>
          </section>
        )}

        {error ? (
          <div className="mt-6 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
            {error}
          </div>
        ) : null}
      </div>
    </div>
  )
}

export default function ShiftSelectionPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-[linear-gradient(180deg,#14311c_0%,#0b180f_100%)] text-white">
          <Spinner className="h-8 w-8 text-[var(--muted-teal)]" />
        </div>
      }
    >
      <ShiftSelectionScreen />
    </Suspense>
  )
}
