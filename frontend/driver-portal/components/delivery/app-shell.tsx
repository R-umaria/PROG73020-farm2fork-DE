"use client"

import { cn } from "@/lib/utils"
import { BottomNav } from "./bottom-nav"

interface AppShellProps {
  children: React.ReactNode
  showNav?: boolean
  className?: string
}

export function AppShell({ children, showNav = true, className }: AppShellProps) {
  return (
    <div className={cn(
      "min-h-screen bg-background",
      showNav && "pb-20",
      className
    )}>
      {children}
      {showNav && <BottomNav />}
    </div>
  )
}
