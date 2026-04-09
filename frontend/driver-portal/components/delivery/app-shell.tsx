"use client"

import { Spinner } from "@/components/ui/spinner"
import { useDriverSession } from "@/hooks/use-driver-session"
import { cn } from "@/lib/utils"
import { BottomNav } from "./bottom-nav"

interface AppShellProps {
  children: React.ReactNode
  showNav?: boolean
  className?: string
}

export function AppShell({ children, showNav = true, className }: AppShellProps) {
  const { isReady, session } = useDriverSession({ required: true })

  if (!isReady || !session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Spinner className="h-8 w-8 text-[var(--muted-teal)]" />
      </div>
    )
  }

  return (
    <div
      className={cn(
        "min-h-screen bg-background",
        showNav && "pb-20",
        className,
      )}
    >
      {children}
      {showNav && <BottomNav />}
    </div>
  )
}
