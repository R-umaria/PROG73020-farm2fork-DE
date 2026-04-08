"use client"

import { deliveryStatusConfig, type DeliveryStatus } from "@/lib/delivery-status"
import { cn } from "@/lib/utils"

interface StatusBadgeProps {
  status: DeliveryStatus
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = deliveryStatusConfig[status]

  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide",
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  )
}
