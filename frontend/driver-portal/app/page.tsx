"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowRight, Eye, EyeOff, Leaf, Truck, UserRoundSearch } from "lucide-react"

import { listDrivers, type DriverSummary } from "@/lib/api-client"
import { getDriverSession, saveDriverSession } from "@/lib/driver-session"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Field, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"

function matchesDriver(driver: DriverSummary, query: string): boolean {
  const normalizedQuery = query.trim().toLowerCase()
  if (!normalizedQuery) {
    return true
  }

  return (
    String(driver.driver_id).includes(normalizedQuery) ||
    driver.driver_name.toLowerCase().includes(normalizedQuery)
  )
}

export default function LoginPage() {
  const router = useRouter()
  const [query, setQuery] = useState("")
  const [dispatchCode, setDispatchCode] = useState("")
  const [showDispatchCode, setShowDispatchCode] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [drivers, setDrivers] = useState<DriverSummary[]>([])
  const [selectedDriverId, setSelectedDriverId] = useState<number | null>(null)
  const [isLoadingDrivers, setIsLoadingDrivers] = useState(true)
  const [isSigningIn, setIsSigningIn] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (getDriverSession()) {
      router.replace("/dashboard")
      return
    }

    const loadDrivers = async () => {
      setIsLoadingDrivers(true)
      setError(null)

      try {
        const roster = await listDrivers()
        setDrivers(roster)
        if (roster.length > 0) {
          setSelectedDriverId(roster[0].driver_id)
        }
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : "Unable to load driver roster.")
      } finally {
        setIsLoadingDrivers(false)
      }
    }

    void loadDrivers()
  }, [router])

  const filteredDrivers = useMemo(
    () => drivers.filter((driver) => matchesDriver(driver, query)),
    [drivers, query],
  )

  const selectedDriver = useMemo(() => {
    if (selectedDriverId !== null) {
      return drivers.find((driver) => driver.driver_id === selectedDriverId) ?? null
    }

    if (filteredDrivers.length === 1) {
      return filteredDrivers[0]
    }

    return null
  }, [drivers, filteredDrivers, selectedDriverId])

  const handleSignIn = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)

    const driver = selectedDriver ?? (filteredDrivers.length === 1 ? filteredDrivers[0] : null)
    if (!driver) {
      setError("Pick a driver profile from the backend roster before continuing.")
      return
    }

    setIsSigningIn(true)
    saveDriverSession(
      {
        driverId: driver.driver_id,
        driverName: driver.driver_name,
        vehicleType: driver.vehicle_type,
        driverStatus: driver.driver_status,
        signedInAt: new Date().toISOString(),
      },
      rememberMe,
    )
    router.push("/dashboard")
  }

  const handleQuickPick = (driver: DriverSummary) => {
    setSelectedDriverId(driver.driver_id)
    setQuery(driver.driver_name)
    setError(null)
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-[var(--evergreen)] via-[var(--evergreen)] to-[#1a3a20]">
      <div className="flex-1 flex flex-col items-center justify-center px-6 pt-12 pb-8">
        <div className="flex items-center justify-center w-20 h-20 bg-[var(--muted-teal)]/20 rounded-2xl mb-6 border border-[var(--muted-teal)]/30">
          <div className="relative">
            <Truck className="w-10 h-10 text-[var(--muted-teal)]" />
            <Leaf className="w-5 h-5 text-[var(--muted-teal)] absolute -top-1 -right-2" />
          </div>
        </div>

        <h1 className="text-3xl font-bold text-white tracking-tight text-balance text-center">Farm2Fork</h1>
        <p className="text-lg text-[var(--muted-teal)] font-medium mt-1">Driver Portal</p>
        <p className="text-sm text-white/60 mt-3 text-center max-w-[280px] text-pretty">
          Sign in with a live driver profile from the backend roster
        </p>

        <div className="flex items-center gap-2 mt-8">
          <div className="w-8 h-[2px] bg-[var(--muted-teal)]/30 rounded-full" />
          <div className="w-2 h-2 bg-[var(--muted-teal)]/50 rounded-full" />
          <div className="w-8 h-[2px] bg-[var(--muted-teal)]/30 rounded-full" />
        </div>
      </div>

      <div className="bg-card rounded-t-[32px] px-6 pt-8 pb-10 shadow-2xl">
        <form onSubmit={handleSignIn} className="max-w-sm mx-auto space-y-5">
          <Field>
            <FieldLabel className="text-sm font-medium text-foreground">Driver ID or Name</FieldLabel>
            <Input
              type="text"
              placeholder="Search the live driver roster"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value)
                setSelectedDriverId(null)
              }}
              className="h-12 bg-background border-border rounded-xl text-base placeholder:text-muted-foreground/60"
            />
          </Field>

          <Field>
            <FieldLabel className="text-sm font-medium text-foreground">Dispatch Code (optional)</FieldLabel>
            <div className="relative">
              <Input
                type={showDispatchCode ? "text" : "password"}
                placeholder="Not enforced until full auth exists"
                value={dispatchCode}
                onChange={(event) => setDispatchCode(event.target.value)}
                className="h-12 bg-background border-border rounded-xl text-base pr-12 placeholder:text-muted-foreground/60"
              />
              <button
                type="button"
                onClick={() => setShowDispatchCode((current) => !current)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showDispatchCode ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                <span className="sr-only">Toggle dispatch code visibility</span>
              </button>
            </div>
          </Field>

          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Checkbox
                id="remember"
                checked={rememberMe}
                onCheckedChange={(checked) => setRememberMe(Boolean(checked))}
                className="border-border data-[state=checked]:bg-[var(--muted-teal)] data-[state=checked]:border-[var(--muted-teal)]"
              />
              <label htmlFor="remember" className="text-sm text-muted-foreground cursor-pointer select-none">
                Remember me
              </label>
            </div>
            <span className="text-xs text-muted-foreground text-right">Uses browser session storage by default</span>
          </div>

          <div className="rounded-2xl border border-border bg-background/60 p-4">
            <div className="flex items-center gap-2 mb-3">
              <UserRoundSearch className="h-4 w-4 text-[var(--twilight-indigo)]" />
              <p className="text-sm font-medium text-foreground">Available drivers</p>
            </div>
            {isLoadingDrivers ? (
              <div className="flex items-center justify-center py-4">
                <Spinner className="h-5 w-5 text-[var(--muted-teal)]" />
              </div>
            ) : filteredDrivers.length === 0 ? (
              <p className="text-sm text-muted-foreground">No driver profiles matched your search.</p>
            ) : (
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {filteredDrivers.map((driver) => {
                  const isSelected = driver.driver_id === selectedDriver?.driver_id
                  return (
                    <button
                      key={driver.driver_id}
                      type="button"
                      onClick={() => handleQuickPick(driver)}
                      className={`w-full rounded-xl border px-3 py-3 text-left transition ${
                        isSelected
                          ? "border-[var(--muted-teal)] bg-[var(--muted-teal)]/10"
                          : "border-border hover:border-[var(--muted-teal)]/40"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="font-medium text-foreground">{driver.driver_name}</p>
                          <p className="text-xs text-muted-foreground">Driver #{driver.driver_id} • {driver.vehicle_type}</p>
                        </div>
                        <span className="text-xs rounded-full px-2 py-1 bg-[var(--thistle)] text-[var(--twilight-indigo)]">
                          {driver.driver_status}
                        </span>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
          </div>

          {error ? <p className="text-sm text-red-600">{error}</p> : null}

          <Button
            type="submit"
            disabled={isSigningIn || isLoadingDrivers || !selectedDriver}
            className="w-full h-12 bg-[var(--muted-teal)] hover:bg-[var(--muted-teal)]/90 text-[var(--evergreen)] font-semibold text-base rounded-xl mt-2 transition-all disabled:opacity-50"
          >
            {isSigningIn ? (
              <Spinner className="w-5 h-5" />
            ) : (
              <>
                Continue as {selectedDriver?.driver_name ?? "driver"}
                <ArrowRight className="w-5 h-5 ml-2" />
              </>
            )}
          </Button>

          <p className="text-center text-xs text-muted-foreground pt-4">
            Need local demo data? Enable <span className="font-medium">DRIVER_SERVICE_ENABLE_DEV_FALLBACK=true</span> in the backend env.
          </p>
        </form>
      </div>
    </div>
  )
}
