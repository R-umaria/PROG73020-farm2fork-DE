"use client"

import { useEffect, useState } from "react"
import { usePathname, useRouter } from "next/navigation"

import {
  clearDriverSession,
  getDriverSession,
  type DriverSession,
} from "@/lib/driver-session"

interface UseDriverSessionOptions {
  required?: boolean
}

export function useDriverSession(options: UseDriverSessionOptions = {}) {
  const { required = false } = options
  const router = useRouter()
  const pathname = usePathname()
  const [session, setSession] = useState<DriverSession | null>(null)
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    const activeSession = getDriverSession()
    setSession(activeSession)
    setIsReady(true)

    if (required && !activeSession && pathname !== "/") {
      router.replace("/")
    }
  }, [pathname, required, router])

  const signOut = () => {
    clearDriverSession()
    setSession(null)
    router.replace("/")
  }

  return {
    session,
    isReady,
    signOut,
  }
}
