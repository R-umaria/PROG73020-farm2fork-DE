"use client"

import { cn } from "@/lib/utils"
import { ArrowLeft, Bell } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

interface PageHeaderProps {
  title: string
  subtitle?: string
  backHref?: string
  showNotifications?: boolean
  actions?: React.ReactNode
  className?: string
}

export function PageHeader({
  title,
  subtitle,
  backHref,
  showNotifications = false,
  actions,
  className
}: PageHeaderProps) {
  return (
    <header className={cn(
      "sticky top-0 z-40 bg-[var(--evergreen)] text-white px-4 py-4 safe-area-inset-top",
      className
    )}>
      <div className="flex items-center justify-between gap-3 max-w-4xl mx-auto">
        <div className="flex items-center gap-3 min-w-0">
          {backHref && (
            <Link href={backHref}>
              <Button 
                variant="ghost" 
                size="icon"
                className="text-white hover:bg-white/10 -ml-2"
              >
                <ArrowLeft className="w-5 h-5" />
                <span className="sr-only">Go back</span>
              </Button>
            </Link>
          )}
          <div className="min-w-0">
            <h1 className="text-lg font-semibold truncate">{title}</h1>
            {subtitle && (
              <p className="text-sm text-white/70 truncate">{subtitle}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {actions}
          {showNotifications && (
            <Button 
              variant="ghost" 
              size="icon"
              className="text-white hover:bg-white/10 relative"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[var(--muted-teal)] rounded-full" />
              <span className="sr-only">Notifications</span>
            </Button>
          )}
        </div>
      </div>
    </header>
  )
}
