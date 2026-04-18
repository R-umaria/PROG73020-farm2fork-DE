"use client"

import { useEffect, useState } from "react"
import { usePathname, useRouter } from "next/navigation"
import { clearDriverSession, getDriverSession, type DriverSession } from "@/lib/driver-session"

interface UseDriverSessionOptions { required?: boolean; requireShift?: boolean }

export function useDriverSession(options: UseDriverSessionOptions = {}) {
  const { required = false, requireShift = false } = options
  const router = useRouter(); const pathname = usePathname()
  const [session, setSession] = useState<DriverSession | null>(null)
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    const activeSession = getDriverSession(); setSession(activeSession); setIsReady(true)
    const missingSession = required && !activeSession && pathname !== "/"
    const missingShift = requireShift && activeSession && !activeSession.selectedShiftId && pathname !== "/"
    if (missingSession || missingShift) router.replace("/")
  }, [pathname, required, requireShift, router])

  const signOut = () => { clearDriverSession(); setSession(null); router.replace("/") }
  return { session, isReady, signOut }
}
