"use client"

import { type DeliveryStatus } from "@/lib/delivery-status"
import { cn } from "@/lib/utils"
import { StatusBadge } from "./status-badge"
import { MapPin, Clock, Package, ChevronRight } from "lucide-react"

interface DeliveryCardProps {
  stopNumber: number
  customerName: string
  address: string
  timeWindow: string
  deliveryType: string
  status: DeliveryStatus
  isActive?: boolean
  onClick?: () => void
  className?: string
}

export function DeliveryCard({
  stopNumber,
  customerName,
  address,
  timeWindow,
  deliveryType,
  status,
  isActive = false,
  onClick,
  className
}: DeliveryCardProps) {
  return (
    <div
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault()
          onClick()
        }
      }}
      className={cn(
        "relative bg-card rounded-xl p-4 transition-all border",
        isActive
          ? "border-[var(--muted-teal)] shadow-lg shadow-[var(--muted-teal)]/10 ring-1 ring-[var(--muted-teal)]/20"
          : "border-border hover:border-[var(--muted-teal)]/50 hover:shadow-md",
        onClick && "cursor-pointer",
        status === "delivered" && "opacity-75",
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn(
          "flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center font-bold text-sm",
          isActive
            ? "bg-[var(--muted-teal)] text-[var(--evergreen)]"
            : status === "delivered"
              ? "bg-[var(--muted-teal)]/20 text-[var(--muted-teal)]"
              : "bg-[var(--twilight-indigo)]/10 text-[var(--twilight-indigo)]"
        )}>
          #{stopNumber}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <h3 className="font-semibold text-foreground truncate">
                {customerName}
              </h3>
              <div className="flex items-center gap-1.5 mt-1 text-sm text-muted-foreground">
                <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
                <span className="truncate">{address}</span>
              </div>
            </div>
            <StatusBadge status={status} />
          </div>

          <div className="flex items-center gap-4 mt-3">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Clock className="w-3.5 h-3.5" />
              <span>{timeWindow}</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Package className="w-3.5 h-3.5" />
              <span>{deliveryType}</span>
            </div>
          </div>
        </div>

        {onClick && (
          <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0 self-center" />
        )}
      </div>

      {isActive && (
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-[var(--muted-teal)] rounded-r-full" />
      )}
    </div>
  )
}
